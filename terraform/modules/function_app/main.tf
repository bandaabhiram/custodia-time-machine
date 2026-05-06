resource "azurerm_storage_account" "functions" {
  name                     = "${var.prefix}func${random_string.suffix.result}"
  resource_group_name      = var.resource_group_name
  location                 = var.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  tags                     = var.tags
}

resource "random_string" "suffix" {
  length  = 8
  special = false
  upper   = false
}

resource "azurerm_service_plan" "functions" {
  name                = "${var.prefix}-asp"
  resource_group_name = var.resource_group_name
  location            = var.location
  os_type             = "Linux"
  sku_name            = "Y1" # Consumption plan
  tags                = var.tags
}

resource "azurerm_linux_function_app" "collectors" {
  name                = "${var.prefix}-collectors-${random_string.suffix.result}"
  resource_group_name = var.resource_group_name
  location            = var.location
  service_plan_id     = azurerm_service_plan.functions.id
  storage_account_name       = azurerm_storage_account.functions.name
  storage_account_access_key = azurerm_storage_account.functions.primary_access_key
  tags                       = var.tags

  site_config {
    application_stack {
      python_version = "3.11"
    }
    application_insights_connection_string = azurerm_application_insights.appinsights.connection_string
  }

  app_settings = {
    "COSMOS_ENDPOINT"             = var.cosmos_db_endpoint
    "COSMOS_KEY"                  = var.cosmos_db_key
    "FUNCTIONS_WORKER_RUNTIME"    = "python"
    "ENABLE_ORYX_BUILD"           = "true"
    "SCM_DO_BUILD_DURING_DEPLOYMENT" = "true"
  }

  identity {
    type = "SystemAssigned"
  }
}

resource "azurerm_application_insights" "appinsights" {
  name                = "${var.prefix}-appinsights"
  resource_group_name = var.resource_group_name
  location            = var.location
  application_type    = "web"
  tags                = var.tags
}

output "function_app_id" {
  value = azurerm_linux_function_app.collectors.id
}

output "function_app_name" {
  value = azurerm_linux_function_app.collectors.name
}
