[繁體中文](architecture.md) | **English**

# Manufacturing Data Quality Monitoring | System Architecture

## Production Architecture

```mermaid
flowchart TB
    A["MES: production, material, and procurement data"]
    B["IT-managed data transfer"]
    C["Data warehouse: critical BOM tables"]
    D["Data quality engine: completeness, schema, nulls, freshness"]
    E["Quality logs: summary, detail, and exception evidence"]
    F["Power BI: status and history"]
    G["Power Automate and Teams: alerts and collaboration"]
    H["BOM platform"]

    A --> B
    B --> C
    C --> H
    C --> D
    D --> E
    E --> F
    F --> G
    D -. "Pre-run warning and post-run diagnosis" .-> H
```

## Component Responsibilities

| Component | Responsibility |
|---|---|
| MES | Produces the production, material, and procurement data required by BOM |
| IT-managed data transfer | Loads source data into the data warehouse on schedule |
| Data warehouse | Provides integrated tables for BOM and other analytical use |
| Data quality engine | Applies table- and field-level rules based on schedule and configuration |
| Quality logs | Stores table summaries and detailed results for every rule |
| Power BI | Presents normal status, warnings, history, and exception details |
| Power Automate and Teams | Converts exceptions into notifications for the responsible teams |
| BOM platform | Uses the data warehouse tables for BOM calculation |

## Validation Workflow

```mermaid
stateDiagram-v2
    state "Wait for Schedule" as Wait
    state "Select Tables" as Select
    state "Load Rules" as Load
    state "Run Checks" as Check
    state "Store Results" as Store
    state "Refresh Dashboard" as Refresh
    state "Send Exception Alert" as Notify
    state "Complete" as Complete

    [*] --> Wait
    Wait --> Select: Monitoring window reached
    Select --> Load: Read table configuration
    Load --> Check: Apply quality rules
    Check --> Store: Save summary and detail
    Store --> Refresh: Update status
    Refresh --> Complete: All checks passed
    Refresh --> Notify: Exception detected
    Notify --> Complete: Relevant teams notified
    Complete --> [*]
```

## Quality Log Model

```mermaid
flowchart LR
    A["Validation batch"] --> B["Table summary"]
    A --> C["Rule detail"]
    B --> D["Normal or warning"]
    C --> E["Field and rule"]
    C --> F["Unexpected count or observed value"]
```

Summary records support dashboards and notifications. Rule-level detail preserves the field, validation type, exception count, and observed value required for diagnosis.

## Architecture Evolution

```mermaid
flowchart TB
    subgraph Before[Initial Architecture]
        A["MES"] --> B["Data transfer"]
        B --> C["Data warehouse"]
        C --> D["BOM"]
        C --> E["Quality monitoring"]
    end

    subgraph Target[Evolved Architecture]
        F["MES source tables"] --> G["BOM"]
        H["Remaining transferred sources"] --> I["Targeted quality monitoring"]
    end

    Before -. "Phased migration" .-> Target
```

The platform is being phased out because direct MES access removes much of the transfer risk it was designed to control. Monitoring remains only for sources that still require an intermediate transfer.

## Diagram Notes

- Solid arrows indicate the primary data or process flow.
- Dashed arrows indicate monitoring feedback or architecture evolution.
- All data sources, tables, and system names are de-identified.
