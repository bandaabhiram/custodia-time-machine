resource "azurerm_virtual_network" "powerbi" {
  name                = "${var.prefix}-pbi-vnet"
  resource_group_name = var.resource_group_name
  location            = var.location
  address_space       = ["10.100.0.0/16"]
  tags                = var.tags
}

resource "azurerm_subnet" "gateway" {
  name                 = "gateway-subnet"
  resource_group_name  = var.resource_group_name
  virtual_network_name = azurerm_virtual_network.powerbi.name
  address_prefixes     = ["10.100.1.0/24"]
}

# VNet integration for Cosmos DB private access
resource "azurerm_cosmosdb_virtual_network_rule" "powerbi" {
  name                = "powerbi-gateway-access"
  resource_group_name = var.resource_group_name
  account_name        = data.azurerm_cosmosdb_account.custodia.name
  virtual_network_id  = azurerm_virtual_network.powerbi.id
  subnet_id           = azurerm_subnet.gateway.id
}

data "azurerm_cosmosdb_account" "custodia" {
  name                = "${var.prefix}-cosmos" # Simplified reference
  resource_group_name = var.resource_group_name
}
