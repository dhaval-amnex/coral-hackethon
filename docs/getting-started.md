What is Coral?
Coral is an open-source data retrieval layer for agents that lets them query any API, database, or file as SQL tables. Here's what it handles for you:

Query anything as SQL: Any API, database, or file becomes a SQL table. No custom integrations needed.
Cross-source joins: Join data across GitHub, Slack, Sentry, PagerDuty, and more in a single SQL query.
Auth & pagination handled: Coral manages authentication, pagination, and rate limits for every source.
Schema learning: Coral automatically learns the schema of your data sources.
Caching: Smart caching so repeated queries are fast.
CLI or MCP: Run Coral from the command line or through MCP. Your choice.
100% local: Credentials, data, and usage history never leave your machine.
No ETL, no warehouse, no glue code: Just SQL queries against live data.

---

> ## Documentation Index
>
> Fetch the complete documentation index at: https://withcoral.com/docs/llms.txt
> Use this file to discover all available pages before exploring further.

# Introduction to Coral

> Coral is a single SQL interface for APIs, files, and other data sources.

<img src="https://mintcdn.com/withcoral/rjjtYcA7TErv9zqt/images/cover.png?fit=max&auto=format&n=rjjtYcA7TErv9zqt&q=85&s=de93662205d6afb050100afbc89be736" alt="Coral cover" width="1692" height="242" data-path="images/cover.png" />

Agents are able to make fewer, more precise tool calls with Coral than they do with data source MCP servers, CLI tools or API wrappers. For agent read tasks, SQL has a structural advantage when query complexity exceeds what a single API call can answer. It avoids pagination through large results, has cleaner, tabular responses, can bring back specific columns, and can correlate across sources more efficiently.

Coral supports a number of [popular data sources](/reference/bundled-sources) bundled in, plus [community source specs](/reference/community-sources) you can import with `coral source add --file`. You can also extend it to accommodate others by writing your own [source specs](/reference/source-spec-reference). You can run SQL from the [CLI](/reference/cli-reference) or through [MCP](/guides/use-coral-over-mcp). And everything is local; your data, credentials and usage history never leave your machine.

## Get started

<Steps titleSize="h3">
  <Step title="Install Coral">
    Install the Coral CLI to get started.

    ```shellscript theme={"theme":{"light":"github-light","dark":"github-dark"}}
    brew install withcoral/tap/coral
    ```

    [See all installation options](/getting-started/installation)

  </Step>

  <Step title="Add your sources">
    Connect GitHub, Slack, Datadog, and other [bundled sources](/reference/bundled-sources) to your workspace. For example:

    ```shellscript theme={"theme":{"light":"github-light","dark":"github-dark"}}
    coral source add --interactive github
    ```

    [Go to the quickstart](/getting-started/quickstart)

  </Step>

  <Step title="Start querying">
    Write SQL directly or let your AI agent query on your behalf.

    ```shellscript theme={"theme":{"light":"github-light","dark":"github-dark"}}
    coral sql "SELECT name, stargazers_count FROM github.org_repos WHERE org = 'withcoral' ORDER BY stargazers_count DESC"
    ```

    [Or use Coral over MCP](/guides/use-coral-over-mcp)

  </Step>
</Steps>

## Why Coral

Most agent workflows access company data one tool at a time. That works, but it tends to create:

- too many tool calls
- repeated auth, pagination, and retry logic
- poor cross-source reasoning
- high token traffic
- brittle glue code and prompts

Coral gives agents one query interface instead:

- query multiple live sources through SQL
- keep workflows inspectable and scriptable
- expose the same runtime over MCP
- answer cross-source questions without stitching tools together by hand

### Benchmark

We benchmarked Coral against direct provider MCPs (Datadog, Sentry, Linear, Slack, and GitHub) for a diverse set of 82 real-world AI tasks using Claude Opus 4.6. Key findings:

1. **Widespread impact on performance.** Across all tasks, Claude was 20% more accurate and 2x more cost efficient using Coral than using direct provider MCPs. With Coral, Claude also had 42% lower latency.
2. **Highest impact on coding agent tasks.** Across the more complex tasks that typify coding agent workloads (multi-hop, higher post-processing), Claude was 31% more accurate and 3.4x more cost efficient with Coral.
3. **More neutral impact on simpler tasks.** For simpler AI tasks, such as raw fact retrieval from knowledge bases, the results were closer, with Claude 6% more accurate and 2% more cost efficient with Coral.

Full [benchmark report](https://withcoral.com/benchmarks).

## How Coral works

Coral sits between your agents and your data sources: your agents write SQL, and Coral translates it into API calls or file reads, then returns a single query result.

You can ask your agents complex questions about your data:

<img src="https://mintcdn.com/withcoral/QX4Qk22OEUpfP_K7/images/claude-query-example.png?fit=max&auto=format&n=QX4Qk22OEUpfP_K7&q=85&s=341cd747aeaf0e0a9fa52ac8f1a5260c" alt="coral sql demo" width="2075" height="829" data-path="images/claude-query-example.png" />

Or run SQL queries yourself:

<img src="https://mintcdn.com/withcoral/V1q8FpaaQbWqCG8N/images/coral-sql-join.gif?s=14875d701b649f18d9835204feea9d7f" alt="coral sql demo" width="1315" height="604" data-path="images/coral-sql-join.gif" />

A **source spec** is a YAML file that defines how to reach an API or local dataset and which tables/columns it exposes. A **source** is a data source Coral can query, created from a source spec plus your configured credentials and variables. When you run `coral source add github`, Coral installs the `github` source. At query time, Coral loads that source as the `github` SQL schema, so tables like `github.issues` and `github.pulls` are queryable. Start with [bundled sources](/reference/bundled-sources), check [community sources](/reference/community-sources), or [write your own](/guides/write-a-custom-source).

During `source add`, Coral collects each declared variable and secret (tokens, workspace IDs, file paths, etc.) from environment variables of the same name, or prompts for them interactively when you pass `--interactive`. These values are stored locally in Coral state, with secrets kept separately from non-secret config, and used only at query time. Because each source appears as SQL tables, you can `JOIN` across sources in one statement (for example `github.issues` with `linear.attachments`), and Coral executes that locally on your machine.

```mermaid actions={false} theme={"theme":{"light":"github-light","dark":"github-dark"}}
graph LR
    Agent["You / your agent"] -->|SQL query| Coral["Coral (local)"]
    Coral -->|Result rows| Agent

    subgraph Sources["Installed sources"]
        GH["github source<br/>(github.* tables)"]
        LN["linear source<br/>(linear.* tables)"]
        FS["file source<br/>(your_files.* tables)"]
    end

    Coral --> GH
    Coral --> LN
    Coral --> FS

    subgraph Backing["Backing systems"]
        GHAPI["GitHub API"]
        LNAPI["Linear API"]
        Disk["Local files"]
    end

    GH -.->|PAT / gh auth token| GHAPI
    LN -.->|Personal API key| LNAPI
    FS -.->|File path| Disk
```

For the full internals, crates, gRPC transport, DataFusion integration, see the [architecture page](/project/architecture).

## Quick links

<CardGroup cols={2}>
  <Card title="Use Coral over MCP" href="/guides/use-coral-over-mcp">
    Set up MCP for Claude Code, Cursor, and other agents
  </Card>

  <Card title="Write a custom source" href="/guides/write-a-custom-source">
    Connect any API or dataset to Coral
  </Card>

  <Card title="Bundled sources" href="/reference/bundled-sources">
    GitHub, Slack, Stripe, and more
  </Card>

  <Card title="Community sources" href="/reference/community-sources">
    Import ClickHouse, Cloudflare, Neon, and other community specs
  </Card>

  <Card title="Source spec reference" href="/reference/source-spec-reference">
    Full YAML field reference for source specs
  </Card>
</CardGroup>
