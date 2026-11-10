# Diagram Type Reference

Annotated syntax examples for each Mermaid diagram type. For diagram selection guidance, see [SKILL.md](../SKILL.md).

## Flowchart

Process flows, decision trees, and algorithms.

```mermaid
flowchart LR
    Start([Start]) --> Validate{Valid?}
    Validate -->|Yes| Process[Process Data]
    Validate -->|No| Error[Return Error]
    Process --> Complete([Done])
```

Key syntax:

- Direction after `flowchart`: `LR`, `TD`, `BT`, `RL`
- Edge labels: `-->|label|`
- Node shapes: `[]` rectangle, `{}` diamond, `([])` stadium, `(())` circle

## Sequence Diagram

API calls, message exchanges, and protocol flows.

```mermaid
sequenceDiagram
    participant Client
    participant API
    participant DB

    Client->>API: POST /users
    activate API
    API->>DB: INSERT user
    DB-->>API: user_id
    API-->>Client: 201 Created
    deactivate API
```

Key syntax:

- `->>` solid arrow, `-->>` dashed reply
- `activate`/`deactivate` for lifeline bars
- `participant` declares ordering; `actor` shows a person icon
- `Note over A,B: text` for spanning notes

## Class Diagram

OOP hierarchies, interfaces, and relationships.

```mermaid
classDiagram
    class Animal {
        +String name
        +int age
        +makeSound() void
    }
    class Dog {
        +fetch() void
    }
    Animal <|-- Dog : extends
```

Key syntax:

- `<|--` inheritance, `*--` composition, `o--` aggregation
- Visibility: `+` public, `-` private, `#` protected, `~` package
- `<<interface>>` and `<<abstract>>` annotations

## State Diagram

State machines, object lifecycles, and workflow states.

```mermaid
stateDiagram-v2
    [*] --> Idle
    Idle --> Processing : submit
    Processing --> Complete : success
    Processing --> Failed : error
    Failed --> Idle : retry
    Complete --> [*]
```

Key syntax:

- `[*]` for start and end states
- `-->` transitions with optional `: event` labels
- `state "Display Name" as s1` for aliased states

## Entity Relationship Diagram

Database schemas and data model relationships.

```mermaid
erDiagram
    USER ||--o{ ORDER : places
    ORDER ||--|{ LINE_ITEM : contains
    LINE_ITEM }o--|| PRODUCT : references

    USER {
        int id PK
        string email UK
        string name
    }
    ORDER {
        int id PK
        int user_id FK
        date created_at
    }
```

Key syntax:

- Cardinality: `||` exactly one, `o|` zero or one, `}|` one or more, `}o` zero or more
- Attributes: `type name [PK|FK|UK]`

## Gantt Chart

Project schedules and timeline planning.

```mermaid
gantt
    title Release Plan
    dateFormat YYYY-MM-DD
    axisFormat %b %d

    section Development
    Feature A       :a1, 2024-01-01, 14d
    Feature B       :a2, after a1, 7d

    section Testing
    Integration     :t1, after a2, 5d
    Release         :milestone, after t1, 0d
```

Key syntax:

- `dateFormat` controls input parsing; `axisFormat` controls display
- Task references: `after taskId` for dependencies
- `:milestone` for zero-duration markers
- `:active`, `:done`, `:crit` for task styling

## Pie Chart

Proportional breakdowns and distribution visualizations.

```mermaid
pie title Language Distribution
    "TypeScript" : 45
    "Python" : 30
    "Go" : 15
    "Other" : 10
```

Key syntax:

- Values are proportional; they do not need to sum to 100.
- Always quote labels to avoid parsing issues.

## Mindmap

Topic hierarchies, brainstorming, and concept maps.

```mermaid
mindmap
    root((Project))
        Frontend
            React
            CSS Modules
        Backend
            Node.js
            PostgreSQL
        DevOps
            GitHub Actions
            Docker
```

Key syntax:

- Indentation defines the tree structure (2 or 4 spaces).
- Root node shape: `(())` circle, `[]` square, `()` rounded.
- Leaf nodes are plain text at indentation level.

## Timeline

Chronological events, milestones, and release history.

```mermaid
timeline
    title Product Milestones
    2023 Q1 : Alpha release
             : Internal testing
    2023 Q2 : Beta release
    2023 Q3 : GA release
             : Documentation complete
```

Key syntax:

- Each time period is followed by `: event` entries.
- Multiple events per period are listed on separate lines with `:` prefix.

## Gitgraph

Branch strategies and merge workflows.

```mermaid
gitGraph
    commit
    branch feature
    checkout feature
    commit
    commit
    checkout main
    merge feature
    commit
```

Key syntax:

- `commit` adds a commit to the current branch
- `branch name` / `checkout name` / `merge name` for branch operations
- `commit id: "msg"` to label specific commits

## Quadrant Chart

Priority matrices and categorization grids.

```mermaid
quadrantChart
    title Task Priority
    x-axis Low Effort --> High Effort
    y-axis Low Impact --> High Impact
    quadrant-1 Do First
    quadrant-2 Schedule
    quadrant-3 Delegate
    quadrant-4 Eliminate
    Task A: [0.8, 0.9]
    Task B: [0.2, 0.3]
    Task C: [0.7, 0.2]
```

Key syntax:

- Coordinates are `[x, y]` in the range `[0, 1]`.
- `quadrant-1` is top-right, numbering goes counter-clockwise.

## XY Chart (Beta)

Line and bar charts with numeric axes.

```mermaid
xychart-beta
    title "Monthly Revenue"
    x-axis [Jan, Feb, Mar, Apr, May]
    y-axis "Revenue (USD)" 0 --> 5000
    bar [1000, 2300, 1800, 4200, 3500]
    line [1000, 2300, 1800, 4200, 3500]
```

Key syntax:

- `x-axis` accepts a label array or numeric range.
- `bar` and `line` accept data arrays of the same length as x-axis.

## Sankey Diagram (Beta)

Flow quantities and resource allocation.

```text
sankey-beta

Source A,Target X,50
Source A,Target Y,30
Source B,Target X,20
Source B,Target Y,40
```

Key syntax:

- CSV format: `source,target,value` (one flow per line).
- Values must be positive numbers.
- Rendered as a Sankey flow diagram; note this is a `beta` type.

## Block Diagram (Beta)

System block diagrams and architecture boxes.

```text
block-beta
    columns 3
    A["Service A"]:1
    B["Service B"]:1
    C["Service C"]:1
    D["Load Balancer"]:3
    D --> A
    D --> B
    D --> C
```

Key syntax:

- `columns N` sets the grid width.
- `name:span` sets how many columns a block spans.

## Architecture Diagram (Beta)

Cloud architecture and service topology.

```text
architecture-beta
    group cloud(cloud)[Cloud Provider]

    service api(server)[API] in cloud
    service db(database)[Database] in cloud
    service cache(server)[Cache] in cloud

    api:R --> L:db
    api:B --> T:cache
```

Key syntax:

- `group name(icon)[Label]` for grouping.
- `service name(icon)[Label] in group` for placing services.
- Edge direction uses compass points: `T` top, `B` bottom, `L` left, `R` right.
