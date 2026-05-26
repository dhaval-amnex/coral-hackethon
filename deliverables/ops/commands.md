# Ops Commands Reference

## Install and verify
coral source discover
coral source list

## Add sources
coral source add --interactive pagerduty
coral source add --interactive github
coral source add --interactive slack
coral source add --interactive datadog

## Validate
coral source test pagerduty
coral source test github
coral source test slack
coral source test datadog

## Catalog introspection
coral sql "SELECT schema_name, table_name FROM coral.tables ORDER BY 1,2"
coral sql "SELECT schema_name, table_name, column_name, data_type FROM coral.columns ORDER BY 1,2,3"
coral sql "SELECT schema_name, table_name, filter_name, mode, required FROM coral.filters ORDER BY 1,2,3"

## Run MCP
coral mcp-stdio

## Optional telemetry
# Configure [otel] in Coral config then run queries and inspect backend traces.
