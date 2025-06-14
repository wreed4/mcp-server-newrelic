# NerdGraph Performance Debugging Guide

A comprehensive guide to using New Relic's NerdGraph API for debugging application performance issues.

## Table of Contents

1. [Introduction](#introduction)
2. [Getting Started](#getting-started)
3. [Authentication & Setup](#authentication--setup)
4. [Core Performance Debugging Patterns](#core-performance-debugging-patterns)
5. [Entity-Based Performance Analysis](#entity-based-performance-analysis)
6. [NRQL Queries for Performance Deep Dives](#nrql-queries-for-performance-deep-dives)
7. [Distributed Tracing Analysis](#distributed-tracing-analysis)
8. [Common Performance Investigation Workflows](#common-performance-investigation-workflows)
9. [Alert Integration for Proactive Monitoring](#alert-integration-for-proactive-monitoring)
10. [Best Practices & Troubleshooting](#best-practices--troubleshooting)

## Introduction

NerdGraph is New Relic's GraphQL API that provides programmatic access to your observability data. This guide focuses specifically on using NerdGraph to debug application performance issues, offering practical queries and workflows that help identify bottlenecks, errors, and optimization opportunities.

### Why Use NerdGraph for Performance Debugging?

- **Programmatic Access**: Automate performance analysis and integrate with your existing tools
- **Cross-Account Queries**: Analyze performance across multiple New Relic accounts
- **Rich Metadata**: Access entity relationships and contextual data not available in the UI
- **Custom Workflows**: Build tailored debugging processes for your specific use cases

## Getting Started

### Prerequisites

- New Relic account with monitoring data
- User API key (found in your New Relic account settings)
- Basic understanding of GraphQL (helpful but not required)

### Endpoints

- **US Region**: `https://api.newrelic.com/graphql`
- **EU Region**: `https://api.eu.newrelic.com/graphql`

### Quick Test Query

```graphql
{
  actor {
    user {
      name
      email
    }
  }
}
```

## Authentication & Setup

### cURL Example

```bash
curl -X POST https://api.newrelic.com/graphql \
  -H 'Content-Type: application/json' \
  -H 'API-Key: YOUR_NEW_RELIC_USER_KEY' \
  -d '{"query": "{ actor { user { name } } }"}'
```

### Python Example

```python
import requests
import json

def query_nerdgraph(query, variables=None):
    url = "https://api.newrelic.com/graphql"
    headers = {
        "Content-Type": "application/json",
        "API-Key": "YOUR_NEW_RELIC_USER_KEY"
    }
    payload = {"query": query}
    if variables:
        payload["variables"] = variables
    
    response = requests.post(url, headers=headers, json=payload)
    return response.json()
```

## Core Performance Debugging Patterns

### 1. Identifying Slow Applications

Find applications with poor performance metrics:

```graphql
{
  actor {
    entitySearch(query: "domain = 'APM' AND type = 'APPLICATION'") {
      results {
        entities {
          name
          guid
          ... on ApmApplicationEntityOutline {
            apmSummary {
              responseTimeAverage
              webResponseTimeAverage
              apdexScore
              errorRate
              throughput
            }
          }
        }
      }
    }
  }
}
```

### 2. Application Health Dashboard Query

Get comprehensive health metrics for a specific application:

```graphql
{
  actor {
    entity(guid: "YOUR_APP_GUID") {
      name
      ... on ApmApplicationEntity {
        apmSummary {
          apdexScore
          errorRate
          responseTimeAverage
          webResponseTimeAverage
          nonWebResponseTimeAverage
          throughput
          webThroughput
          nonWebThroughput
        }
        recentAlertViolations {
          agentUrl
          alertSeverity
          closedAt
          label
          level
          openedAt
        }
      }
    }
  }
}
```

### 3. Finding Performance Bottlenecks

Query for high-latency transactions:

```graphql
{
  actor {
    account(id: YOUR_ACCOUNT_ID) {
      nrql(query: "SELECT average(duration), percentile(duration, 95, 99) FROM Transaction WHERE appName = 'YourAppName' FACET name SINCE 1 hour ago LIMIT 20") {
        results
      }
    }
  }
}
```

## Entity-Based Performance Analysis

### 1. Entity Relationship Mapping

Understand service dependencies for performance issues:

```graphql
{
  actor {
    entity(guid: "YOUR_APP_GUID") {
      name
      relatedEntities {
        results {
          source {
            entity {
              name
              guid
              entityType
            }
          }
          target {
            entity {
              name
              guid
              entityType
            }
          }
          type
        }
      }
    }
  }
}
```

### 2. Infrastructure Impact Analysis

Check if performance issues correlate with infrastructure problems:

```graphql
{
  actor {
    entitySearch(query: "domain = 'INFRA' AND type = 'HOST'") {
      results {
        entities {
          name
          guid
          ... on InfrastructureHostEntityOutline {
            hostSummary {
              cpuUtilizationPercent
              memoryUsedPercent
              diskUsedPercent
              networkReceiveRate
              networkTransmitRate
            }
          }
        }
      }
    }
  }
}
```

### 3. Database Performance Analysis

Identify database-related performance issues:

```graphql
{
  actor {
    account(id: YOUR_ACCOUNT_ID) {
      nrql(query: "SELECT average(databaseDuration), count(*), percentage(count(*), WHERE databaseDuration > 1) FROM Transaction WHERE appName = 'YourAppName' FACET databaseType SINCE 1 hour ago") {
        results
      }
    }
  }
}
```

## NRQL Queries for Performance Deep Dives

### 1. Error Rate Analysis

```graphql
{
  actor {
    account(id: YOUR_ACCOUNT_ID) {
      nrql(query: "SELECT count(*) as 'Total Requests', filter(count(*), WHERE error IS true) as 'Errors', percentage(count(*), WHERE error IS true) as 'Error Rate' FROM Transaction WHERE appName = 'YourAppName' TIMESERIES SINCE 6 hours ago") {
        results
      }
    }
  }
}
```

### 2. Apdex Score Trends

```graphql
{
  actor {
    account(id: YOUR_ACCOUNT_ID) {
      nrql(query: "SELECT apdex(duration, t: 0.5) FROM Transaction WHERE appName = 'YourAppName' TIMESERIES SINCE 24 hours ago") {
        results
      }
    }
  }
}
```

### 3. Throughput vs Response Time Correlation

```graphql
{
  actor {
    account(id: YOUR_ACCOUNT_ID) {
      nrql(query: "SELECT rate(count(*), 1 minute) as 'Throughput', average(duration) as 'Response Time' FROM Transaction WHERE appName = 'YourAppName' TIMESERIES SINCE 2 hours ago") {
        results
      }
    }
  }
}
```

### 4. External Service Performance

```graphql
{
  actor {
    account(id: YOUR_ACCOUNT_ID) {
      nrql(query: "SELECT average(duration), count(*) FROM Span WHERE category = 'http' AND span.kind = 'client' FACET `service.name`, `http.url` SINCE 1 hour ago LIMIT 50") {
        results
      }
    }
  }
}
```

### 5. Memory and CPU Correlation

```graphql
{
  actor {
    account(id: YOUR_ACCOUNT_ID) {
      nrql(query: "SELECT average(apm.service.memory.heap.used), average(apm.service.cpu.usertime.utilization) FROM Metric WHERE appName = 'YourAppName' TIMESERIES SINCE 2 hours ago") {
        results
      }
    }
  }
}
```

## Distributed Tracing Analysis

### 1. Find Slow Traces

```graphql
{
  actor {
    account(id: YOUR_ACCOUNT_ID) {
      nrql(query: "SELECT traceId, duration FROM Span WHERE transactionName = 'YourSlowTransaction' AND duration > 1000 SINCE 1 hour ago LIMIT 10") {
        results
      }
    }
  }
}
```

### 2. Detailed Trace Analysis

```graphql
{
  actor {
    distributedTracing {
      trace(traceId: "YOUR_TRACE_ID") {
        id
        timestamp
        durationMs
        spans {
          name
          durationMs
          parentId
          processBoundary
          entityGuid
          spanAnomalies {
            anomalousValue
            anomalyType
            averageMeasure
          }
        }
        entities {
          name
          guid
          entityType
        }
      }
    }
  }
}
```

### 3. Span Relationship Analysis

```graphql
{
  actor {
    distributedTracing {
      trace(traceId: "YOUR_TRACE_ID") {
        spanConnections {
          parent
          child
        }
        spans {
          id
          name
          durationMs
          attributes
        }
      }
    }
  }
}
```

## Common Performance Investigation Workflows

### Workflow 1: Application Performance Regression

1. **Identify the affected application**:
```graphql
{
  actor {
    entitySearch(query: "domain = 'APM' AND alertSeverity IN ('CRITICAL', 'WARNING')") {
      results {
        entities {
          name
          guid
          alertSeverity
        }
      }
    }
  }
}
```

2. **Check recent performance trends**:
```graphql
{
  actor {
    account(id: YOUR_ACCOUNT_ID) {
      nrql(query: "SELECT average(duration), apdex(duration, t: 0.5), percentage(count(*), WHERE error IS true) FROM Transaction WHERE appName = 'YourAppName' TIMESERIES SINCE 24 hours ago COMPARE WITH 1 week ago") {
        results
      }
    }
  }
}
```

3. **Analyze error patterns**:
```graphql
{
  actor {
    account(id: YOUR_ACCOUNT_ID) {
      nrql(query: "SELECT count(*), latest(timestamp) FROM TransactionError WHERE appName = 'YourAppName' FACET `error.class`, `error.message` SINCE 6 hours ago") {
        results
      }
    }
  }
}
```

### Workflow 2: Database Performance Investigation

1. **Check database query performance**:
```graphql
{
  actor {
    account(id: YOUR_ACCOUNT_ID) {
      nrql(query: "SELECT average(duration), count(*), max(duration) FROM Span WHERE category = 'datastore' FACET `db.statement` SINCE 1 hour ago LIMIT 20") {
        results
      }
    }
  }
}
```

2. **Database connection analysis**:
```graphql
{
  actor {
    account(id: YOUR_ACCOUNT_ID) {
      nrql(query: "SELECT uniqueCount(databaseConnectionPoolName), average(databasePool) FROM Transaction WHERE appName = 'YourAppName' TIMESERIES SINCE 2 hours ago") {
        results
      }
    }
  }
}
```

### Workflow 3: External Service Impact Analysis

1. **External service response times**:
```graphql
{
  actor {
    account(id: YOUR_ACCOUNT_ID) {
      nrql(query: "SELECT average(duration), count(*), percentile(duration, 95) FROM Span WHERE category = 'http' AND span.kind = 'client' FACET `service.name` SINCE 1 hour ago") {
        results
      }
    }
  }
}
```

2. **Cross-service error correlation**:
```graphql
{
  actor {
    account(id: YOUR_ACCOUNT_ID) {
      nrql(query: "SELECT count(*) FROM Span WHERE category = 'http' AND `http.statusCode` >= 400 FACET `service.name`, `http.statusCode` SINCE 1 hour ago") {
        results
      }
    }
  }
}
```

## Alert Integration for Proactive Monitoring

### 1. Get Active Alert Violations

```graphql
{
  actor {
    account(id: YOUR_ACCOUNT_ID) {
      alerts {
        violationsSearch {
          violations {
            violationId
            label
            policyName
            openedAt
            entity {
              name
              guid
            }
          }
        }
      }
    }
  }
}
```

### 2. Performance Baseline Queries

```graphql
{
  actor {
    account(id: YOUR_ACCOUNT_ID) {
      nrql(query: "SELECT percentile(duration, 50, 95, 99) as 'Response Time Percentiles', apdex(duration, t: 0.5) as 'Apdex', percentage(count(*), WHERE error IS true) as 'Error Rate' FROM Transaction WHERE appName = 'YourAppName' SINCE 1 week ago") {
        results
      }
    }
  }
}
```

## Best Practices & Troubleshooting

### Query Optimization

1. **Use specific time ranges**: Always include `SINCE` clauses to limit data scope
2. **Leverage entity GUIDs**: More efficient than searching by name
3. **Paginate large results**: Use cursor pagination for entity searches
4. **Cache frequently used queries**: Store entity GUIDs and other static data

### Common Pitfalls

1. **Rate limiting**: Respect API rate limits (25 requests per second)
2. **Query timeouts**: Break down complex queries into smaller ones
3. **Data retention**: Be aware of your account's data retention policies
4. **Permission levels**: Ensure your API key has necessary permissions

### Performance Query Templates

#### High-Level Health Check
```graphql
{
  actor {
    entity(guid: "YOUR_APP_GUID") {
      ... on ApmApplicationEntity {
        name
        apmSummary {
          apdexScore
          errorRate
          responseTimeAverage
          throughput
        }
        recentAlertViolations(count: 5) {
          label
          openedAt
          alertSeverity
        }
      }
    }
  }
}
```

#### Detailed Performance Analysis
```graphql
{
  actor {
    account(id: YOUR_ACCOUNT_ID) {
      nrql(query: "SELECT histogram(duration, width: 50, buckets: 20), average(duration), percentile(duration, 50, 95, 99), count(*), percentage(count(*), WHERE error IS true) FROM Transaction WHERE appName = 'YourAppName' SINCE 1 hour ago") {
        results
      }
    }
  }
}
```

### Troubleshooting Tips

1. **Start broad, then narrow**: Begin with entity-level queries, then drill down
2. **Compare time periods**: Use `COMPARE WITH` in NRQL for trend analysis
3. **Use faceting wisely**: Facet by relevant dimensions like transaction name, host, etc.
4. **Leverage distributed tracing**: For complex, multi-service issues
5. **Monitor infrastructure correlation**: Performance issues often have infrastructure causes

### Advanced Techniques

#### Custom Metrics Analysis
```graphql
{
  actor {
    account(id: YOUR_ACCOUNT_ID) {
      nrql(query: "SELECT latest(yourCustomMetric), average(yourCustomMetric) FROM Metric WHERE metricName = 'custom.performance.metric' TIMESERIES SINCE 2 hours ago") {
        results
      }
    }
  }
}
```

#### Multi-Account Performance Comparison
```graphql
{
  actor {
    nrql(
      accounts: [ACCOUNT_ID_1, ACCOUNT_ID_2]
      query: "SELECT average(duration), count(*) FROM Transaction FACET appName SINCE 1 hour ago"
    ) {
      results
    }
  }
}
```

This guide provides a foundation for using NerdGraph to debug application performance issues. Adapt these patterns to your specific use cases and monitoring requirements.