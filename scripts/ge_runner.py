import yaml
import datetime
import os
import urllib
from sqlalchemy import create_engine
from great_expectations.dataset import SqlAlchemyDataset
from dotenv import load_dotenv
from dglib.db.dbutils import DB
from config import GlobalVar

class DataQuality:

    def __init__(self):
        load_dotenv()
        self.now = datetime.datetime.now()
        self.today = datetime.date.today()
        self.todaytime = datetime.datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
        self.tomorrow = self.today + datetime.timedelta(days=1)
        self.today_sub_1hr = self.todaytime - datetime.timedelta(hours=1)
        self.today_str = format(self.today, '%Y-%m-%d')
        self.tomorrow_str = format(self.tomorrow, '%Y-%m-%d')
        self.today_sub_1hr_str = format(self.today_sub_1hr, '%Y-%m-%dT%H:%M:%S')

    def build_conn_str(self, ds_conf):
        user = os.getenv(ds_conf["user_env"])
        password = os.getenv(ds_conf["password_env"])
        host = os.getenv(ds_conf["host_env"])
        dbname = os.getenv(ds_conf["dbname_env"])
        driver = os.getenv(ds_conf["driver_env"])
        conn_str = f'''DRIVER={driver};SERVER={host};DATABASE={dbname};UID={user};PWD={password}'''
        params = urllib.parse.quote_plus(conn_str)
        
        return f"mssql+pyodbc:///?odbc_connect={params}"

    def load_expectation_yaml(self, path: str):
        with open(path, "r", encoding="utf-8") as f:
            yml = yaml.safe_load(f)

        i = 0
        for e in yml["expectations"]:
            yml["expectations"][i] = self.replace_date(e)
            i += 1

        return yml

    def replace_date(self, data):
        if isinstance(data, dict):
            return {k: self.replace_date(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self.replace_date(i) for i in data]
        elif isinstance(data, str):
            if data == 'min_date':
                return self.today_sub_1hr_str
            elif data == 'max_date':
                return self.tomorrow_str
            else:
                return data
        else:
            return data

    def apply_expectations(self, dataset, expectations):
        for e in expectations:
            exp_type = e["expectation_type"]
            kwargs = e["kwargs"]
            getattr(dataset, exp_type)(**kwargs)

    def read_config(self):
        with open("config.yaml", "r", encoding="utf-8") as f:
            self.config = yaml.safe_load(f)

    def is_time_in_range(self, start_str, end_str, now_time):
        fmt = "%H:%M"
        start = datetime.datetime.strptime(start_str, fmt).time()
        end = datetime.datetime.strptime(end_str, fmt).time()
        return start <= now_time <= end

    def get_tables_to_run(self, schedule_config, current_time):
        for item in schedule_config:
            start = item["time_range"]["start"]
            end = item["time_range"]["end"]
            if self.is_time_in_range(start, end, current_time.time()):
                return item["tables"]
        return []

    def check(self):
        self.read_config()
        datasources = self.config["datasources"]
        tables = self.get_tables_to_run(self.config["schedule"], self.now) 

        self.check_res = {}
        for tbl in tables:
            ds_key = tbl["datasource"]
            ds_config = datasources[ds_key]
            conn_str = self.build_conn_str(ds_config)

            engine = create_engine(conn_str)

            table_name = tbl["name"]
            custom_sql = tbl.get("custom_sql")
            expectations = []
            for exp_file in tbl["expectation_files"]:
                yml = self.load_expectation_yaml(exp_file)
                expectations.extend(yml["expectations"])

            print(f"\n🧪 檢查資料表：{table_name} (來自 {ds_key})")
            dataset = None
            if custom_sql:
                dataset = SqlAlchemyDataset(custom_sql=custom_sql, engine=engine)
            else:
                dataset = SqlAlchemyDataset(table_name=table_name, engine=engine)

            self.apply_expectations(dataset, expectations)

            result = dataset.validate()
            print(f"✅ 結果：{result['success']}")
            for r in result["results"]:
                etype = r['expectation_config']['expectation_type']
                print(f" - {etype}: {'✅' if r['success'] else '❌'}")

            self.check_res[table_name] = {
                'datasource':ds_key,
                'result':result
            }

    def res_summary_insert(self):

        list_of_params = []
        event = 'BIDATA資料表檢核'
        muser = 'ur08173'

        for table_name, level_1 in self.check_res.items():
            level_2 = level_1['result']
            success = level_2['success']
            status = 'Info' if success else 'Warning'
            notes = '資料檢核異常' if not success else '資料檢核正常'
            batch_id = level_2['meta']['batch_kwargs']['ge_batch_id']
            run_time = level_2['meta']['run_id'].run_time + datetime.timedelta(hours=8)
            run_time = format(run_time, '%Y-%m-%d %H:%M:%S')

            param = {
                'datetime':run_time,
                'event':event,
                'item':table_name,
                'level':status,
                'notes':notes,
                'batch_id':batch_id,
                'muser':muser
            }
            list_of_params.append(param)

        sqlstr = '''
        insert into YS_Material_PCI_Log
        (Datetime,Event,Item,Level,Notes,Batch_Id,MUser)
        values(:datetime,:event,:item,:level,:notes,:batch_id,:muser)
        '''
        DB.execute(sqlstr, conn_str=GlobalVar.QUANTDATA_CONNSTR, params=list_of_params)

    def res_detail_insert(self):

        list_of_params = []

        for table_name, level_1 in self.check_res.items():
            datasource = level_1['datasource']
            level_2 = level_1['result']
            batch_id = level_2['meta']['batch_kwargs']['ge_batch_id']
            run_time = level_2['meta']['run_id'].run_time + datetime.timedelta(hours=8)
            run_time = format(run_time, '%Y-%m-%d %H:%M:%S')
            run_date = run_time[:10]
            expectation_results = level_2['results']
            for res in expectation_results:
                result = 'Y' if res['success'] else 'N'
                expectation_name = res['expectation_config']['expectation_type']
                column = res['expectation_config']['kwargs'].get('column')
                unexpected_count = res.get('result',{}).get('unexpected_count')
                details = res.get('result',{}).get('observed_value')

                param = {
                    'table_name':table_name,
                    'datasource':datasource,
                    'run_date':run_date,
                    'run_time':run_time,
                    'expectation_name':expectation_name,
                    'column_name':column,
                    'result':result,
                    'unexpected_count':unexpected_count,
                    'details':details,
                    'batch_id':batch_id
                }
                list_of_params.append(param)

        sqlstr = '''
        insert into DataQualityCheckLog
        (table_name,datasource,run_date,run_time,expectation_name,column_name,result,unexpected_count,details,batch_id)
        values(:table_name,:datasource,:run_date,:run_time,:expectation_name,:column_name,:result,:unexpected_count,:details,:batch_id)
        '''
        DB.execute(sqlstr, conn_str=GlobalVar.QUANTDATA_CONNSTR, params=list_of_params)
            

if __name__ == "__main__":
    
    dq = DataQuality()
    dq.check()