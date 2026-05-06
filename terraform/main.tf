terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.80"
    }
  }
  backend "azurerm" {
    resource_group_name  = "tfstate-rg"
    storage_account_name = "custodiatfstate"
    container_name       = "tfstate"
    key                  = "custodia.tfstate"
    use_oidc             = true
  }
}

provider "azurerm" {
  features {}
  use_oidc = true
}

locals {
  prefix   = "custodia"
  location = var.location
  tags = {
    project     = "custodia-time-machine"
    managed_by  = "terraform"
    environment = var.environment
  }
}

resource "azurerm_resource_group" "custodia" {
  name     = "${local.prefix}-rg-${var.environment}"
  location = local.location
  tags     = local.tags
}

module "cosmos_db" {
  source              = "./modules/cosmos_db"
  resource_group_name = azurerm_resource_group.custodia.name
  location            = local.location
  prefix              = local.prefix
  tags                = local.tags
}

module "event_grid" {
  source              = "./modules/event_grid"
  resource_group_name = azurerm_resource_group.custodia.name
  location            = local.location
  prefix              = local.prefix
  tags                = local.tags
  function_app_id     = module.function_app.function_app_id
}

module "function_app" {
  source              = "./modules/function_app"
  resource_group_name = azurerm_resource_group.custodia.name
  location            = local.location
  prefix              = local.prefix
  tags                = local.tags
  cosmos_db_endpoint  = module.cosmos_db.endpoint
  cosmos_db_key       = module.cosmos_db.primary_key
}

module "powerbi_gateway" {
  source              = "./modules/powerbi_gateway"
  resource_group_name = azurerm_resource_group.custodia.name
  location            = local.location
  prefix              = local.prefix
  tags                = local.tags
  cosmos_db_endpoint  = module.cosmos_db.endpoint
}

variable "location" {
  description = "Azure region"
  type        = string
  default     = "uksouth"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "prod"
}

variable "subscription_id" {
  description = "Target Azure subscription"
  type        = string
}

output "cosmos_db_endpoint" {
  value = module.cosmos_db.endpoint
}

output "function_app_name" {
  value = module.function_app.function_app_name
}
