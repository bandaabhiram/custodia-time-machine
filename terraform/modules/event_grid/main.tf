resource "azurerm_eventgrid_system_topic" "activity_logs" {
  name                   = "${var.prefix}-activity-topic"
  resource_group_name    = var.resource_group_name
  location               = var.location
  source_arm_resource_id = data.azurerm_subscription.current.id
  topic_type             = "Microsoft.Resources.Subscriptions"
  tags                   = var.tags
}

resource "azurerm_eventgrid_event_subscription" "write_events" {
  name                  = "${var.prefix}-write-subscription"
  scope                 = azurerm_eventgrid_system_topic.activity_logs.id
  event_delivery_schema = "EventGridSchema"

  azure_function_endpoint {
    function_id = "${var.function_app_id}/functions/ActivityLogTrigger"
  }

  included_event_types = [
    "Microsoft.Resources.ResourceWriteSuccess",
    "Microsoft.Resources.ResourceDeleteSuccess"
  ]

  retry_policy {
    max_delivery_attempts = 3
    event_time_to_live    = 1440
  }
}

data "azurerm_subscription" "current" {}
