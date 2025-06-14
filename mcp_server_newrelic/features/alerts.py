import json
from typing import Optional, Dict, Any
from fastmcp import FastMCP

from .. import client
from .. import config

def register(mcp: FastMCP):
    """Registers Alerts-related tools."""

    @mcp.tool() # Was resource
    def list_alert_policies(target_account_id: Optional[int] = None, policy_name_filter: Optional[str] = None) -> str:
        """
        Lists alert policies for the specified or default account, optionally filtering by name.

        Args:
            target_account_id: The account ID to query. Uses default if omitted.
            policy_name_filter: Filter policies where the name contains this string (case-insensitive).

        Returns:
            JSON string containing a list of alert policies or errors.
        """
        account_to_use = target_account_id if target_account_id is not None else config.ACCOUNT_ID
        if not account_to_use:
             return json.dumps({"errors": [{"message": "Account ID must be provided."}]})

        query = """
        query ($accountId: Int!, $cursor: String, $policyName: String) {
          actor {
            account(id: $accountId) {
              alerts {
                policiesSearch(cursor: $cursor, searchCriteria: {name: $policyName}) {
                  policies {
                    id
                    name
                    incidentPreference # PER_POLICY, PER_CONDITION, PER_CONDITION_AND_TARGET
                  }
                  nextCursor # Add pagination handling if needed
                  totalCount
                }
              }
            }
          }
        }
        """
        # Note: This query might need pagination for large numbers of policies.
        variables: Dict[str, Any] = {"accountId": account_to_use}
        if policy_name_filter:
             variables["policyName"] = policy_name_filter # Add filter only if provided

        result = client.execute_nerdgraph_query(query, variables)
        return client.format_json_response(result)


    @mcp.tool() # Was resource
    def list_open_violations(target_account_id: Optional[int] = None, priority: Optional[str] = None) -> str:
        """
        Lists currently alerting entities as proxy for open violations.

        Note: This replaces the deprecated incidents query which is no longer supported
        in the New Relic NerdGraph schema. Returns entities with active alert conditions
        as a proxy for violations since direct violation queries are not available.

        Filters out entities with 'NOT_ALERTING' and 'NOT_CONFIGURED' severities to show
        only entities with actual alert conditions that are currently firing.

        Args:
            target_account_id: The account ID to query. Uses default if omitted.
            priority: Filter by alert severity level (e.g., 'CRITICAL', 'WARNING'). Must be uppercase.

        Returns:
            JSON string containing alerting entities formatted as violations.
        """
        account_to_use = target_account_id if target_account_id is not None else config.ACCOUNT_ID
        if not account_to_use:
             return json.dumps({"errors": [{"message": "Account ID must be provided."}]})

        valid_priorities = ["CRITICAL", "WARNING"]  # New Relic alert severities (excluding NOT_ALERTING, NOT_CONFIGURED)
        if priority and priority.upper() not in valid_priorities:
             return json.dumps({"errors": [{"message": f"Invalid priority '{priority}'. Valid priorities: {valid_priorities}"}]})

        query = """
        query {
          actor {
            entitySearch(queryBuilder: {domain: APM, type: APPLICATION}) {
              results {
                entities {
                  guid
                  name
                  alertSeverity
                }
              }
            }
          }
        }
        """

        result = client.execute_nerdgraph_query(query, {})

        # Post-process to filter entities with alerts as proxy for violations
        if result and 'data' in result:
            try:
                entities = result['data']['actor']['entitySearch']['results']['entities']
                violations = []

                for entity in entities:
                    # Treat alerting entities as violations
                    alert_severity = entity.get('alertSeverity')
                    if alert_severity and alert_severity not in ['NOT_ALERTING', 'NOT_CONFIGURED']:
                        # Apply priority filter if specified
                        if priority is None or alert_severity.upper() == priority.upper():
                            violation = {
                                'violationId': f"entity_{entity.get('guid')}",
                                'label': f"Alert condition on {entity.get('name')}",
                                'level': alert_severity,
                                'openedAt': None,
                                'closedAt': None,
                                'entity': {
                                    'guid': entity.get('guid'),
                                    'name': entity.get('name'),
                                    'alertSeverity': alert_severity
                                }
                            }
                            violations.append(violation)

                return json.dumps({
                    'data': {
                        'violations': violations,
                        'total_count': len(violations)
                    }
                }, indent=2)

            except (KeyError, TypeError) as e:
                return json.dumps({"errors": [{"message": f"Error processing alert data: {str(e)}"}]})

        return client.format_json_response(result)

    # @mcp.tool()
    def acknowledge_alert_incident(incident_id: int, target_account_id: Optional[int] = None, message: Optional[str] = None) -> str:
        """
        Acknowledges an open alert incident.

        Args:
            incident_id: The ID of the incident to acknowledge (integer).
            target_account_id: The account ID where the incident occurred. Uses default if omitted.
            message: Optional message to include with the acknowledgement.

        Returns:
            JSON string with the result of the acknowledgement mutation or errors.
        """
        account_to_use = target_account_id if target_account_id is not None else config.ACCOUNT_ID
        if not account_to_use:
             return json.dumps({"errors": [{"message": "Account ID must be provided."}]})
        if not isinstance(incident_id, int) or incident_id <= 0:
             return json.dumps({"errors": [{"message": "Valid positive integer incident_id is required."}]})

        mutation = """
        mutation ($accountId: Int!, $incidentId: Int!, $message: String) {
          alertsIncidentAcknowledge(accountId: $accountId, incidentId: $incidentId, message: $message) {
            incident {
              incidentId
              state # Should transition to ACKNOWLEDGED
              acknowledgedBy
              acknowledgedAt
              title
            }
            errors {
              description
              type
            }
          }
        }
        """
        variables: Dict[str, Any] = {"accountId": account_to_use, "incidentId": incident_id}
        if message:
            variables["message"] = message

        result = client.execute_nerdgraph_query(mutation, variables)
        return client.format_json_response(result)

    # Add tools for:
    # - Creating/Managing Alert Policies/Conditions/Notification Channels
    # - Closing violations
    # Note: Incident acknowledgement is kept for backward compatibility
