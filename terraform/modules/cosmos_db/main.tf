resource "azurerm_cosmosdb_account" "custodia" {
  name                = "${var.prefix}-cosmos-${random_string.unique.result}"
  location            = var.location
  resource_group_name = var.resource_group_name
  offer_type          = "Standard"
  kind                = "GlobalDocumentDB"
  tags                = var.tags

  enable_free_tier = false

  consistency_policy {
    consistency_level       = "Session"
    max_interval_in_seconds = 5
    max_staleness_prefix    = 100
  }

  geo_location {
    location          = var.location
    failover_priority = 0
  }

  capabilities {
    name = "EnableServerless"
  }
}

resource "random_string" "unique" {
  length  = 8
  special = false
  upper   = false
}

resource "azurerm_cosmosdb_sql_database" "snapshots" {
  name                = "security-snapshots"
  resource_group_name = var.resource_group_name
  account_name        = azurerm_cosmosdb_account.custodia.name
}

resource "azurerm_cosmosdb_sql_container" "configs" {
  name                  = "config-snapshots"
  resource_group_name   = var.resource_group_name
  account_name          = azurerm_cosmosdb_account.custodia.name
  database_name         = azurerm_cosmosdb_sql_database.snapshots.name
  partition_key_path    = "/subscriptionId"
  partition_key_version = 2

  default_ttl = 31536000 # 1 year

  indexing_policy {
    indexing_mode = "consistent"
    included_path { path = "/*" }
    excluded_path { path = "/\"_etag\"/?" }
  }
}

resource "azurerm_cosmosdb_sql_container" "rbac" {
  name                  = "rbac-snapshots"
  resource_group_name   = var.resource_group_name
  account_name          = azurerm_cosmosdb_account.custodia.name
  database_name         = azurerm_cosmosdb_sql_database.snapshots.name
  partition_key_path    = "/subscriptionId"
  partition_key_version = 2
  default_ttl           = 31536000
}

output "endpoint" {
  value = azurerm_cosmosdb_account.custodia.endpoint
}

output "primary_key" {
  value     = azurerm_cosmosdb_account.custodia.primary_key
  sensitive = true
}
