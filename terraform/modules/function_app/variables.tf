variable "resource_group_name" { type = string }
variable "location" { type = string }
variable "prefix" { type = string }
variable "tags" { type = map(string) }
variable "cosmos_db_endpoint" { type = string }
variable "cosmos_db_key" { type = string sensitive = true }
