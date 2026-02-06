# FortiMonitor API Complete Documentation

**Base URL:** `https://api2.panopta.com/v2`

**Total Endpoints:** 33
**Successfully Retrieved:** 33
**Failed:** 0

---

## Table of Contents

- [account_history](#account-history)
- [agent_resource_type](#agent-resource-type)
- [cloud_credential](#cloud-credential)
- [cloud_provider](#cloud-provider)
- [cloud_region](#cloud-region)
- [cloud_service](#cloud-service)
- [compound_service](#compound-service)
- [contact](#contact)
- [contact_group](#contact-group)
- [contact_type](#contact-type)
- [dashboard](#dashboard)
- [dem_application](#dem-application)
- [fabric_connection](#fabric-connection)
- [historical_outage](#historical-outage)
- [maintenance_schedule](#maintenance-schedule)
- [monitoring_node](#monitoring-node)
- [network_service_type](#network-service-type)
- [notification_schedule](#notification-schedule)
- [onsight](#onsight)
- [onsight_group](#onsight-group)
- [outage](#outage)
- [prometheus_resource](#prometheus-resource)
- [public](#public)
- [role](#role)
- [rotating_contact](#rotating-contact)
- [server](#server)
- [server_attribute_type](#server-attribute-type)
- [server_group](#server-group)
- [server_template](#server-template)
- [snmp_credential](#snmp-credential)
- [status_page](#status-page)
- [timezone](#timezone)
- [user](#user)

---

<a name="account-history"></a>
## account_history

### /account_history

**GET - AccountHistory**

Get account historys

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `full` |  |  | If set to true, resolves all urls to actual objects |
| `limit` |  |  | The number of returned items per page; set to 0 to get available data altogether (used for pagination) |
| `offset` |  |  | The beginning index of the item being returned in the list (used for pagination) |
| `order_by` |  |  | The name of the field to sort on; must be an integer, float, boolean, string, or date field |
| `order` |  |  | The sort order for the result set, specified in conjunction with the order_by parameter |
| `end_time` |  | ✓ | End_time in UTC; format: YYYY-MM-DD HH:MM:SS |
| `start_time` |  | ✓ | Start_time in UTC; format: YYYY-MM-DD HH:MM:SS |


---

<a name="agent-resource-type"></a>
## agent_resource_type

### /agent_resource_type

**GET - AgentResourceType**

Get agent resource types

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `full` |  |  | If set to true, resolves all urls to actual objects |
| `limit` |  |  | The number of returned items per page; set to 0 to get available data altogether (used for pagination) |
| `offset` |  |  | The beginning index of the item being returned in the list (used for pagination) |
| `order_by` |  |  | The name of the field to sort on; must be an integer, float, boolean, string, or date field |
| `order` |  |  | The sort order for the result set, specified in conjunction with the order_by parameter |
| `label` |  |  | Filter results by label |
| `resource_textkey` |  |  | Filter results by resource_textkey |
| `platform` |  |  | Filter results by platform |
| `category` |  |  | Filter results by category |


### /agent_resource_type/{agent_resource_type_id}

**GET - AgentResourceType**

Get agent resource type

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `agent_resource_type_id` |  | ✓ | Agent resource type id |
| `full` |  |  | If set to true, resolves all urls to actual objects |


---

<a name="cloud-credential"></a>
## cloud_credential

### /cloud_credential

**GET - CloudCredential**

Get cloud credentials

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `full` |  |  | If set to true, resolves all urls to actual objects |
| `limit` |  |  | The number of returned items per page; set to 0 to get available data altogether (used for pagination) |
| `offset` |  |  | The beginning index of the item being returned in the list (used for pagination) |
| `order_by` |  |  | The name of the field to sort on; must be an integer, float, boolean, string, or date field |
| `order` |  |  | The sort order for the result set, specified in conjunction with the order_by parameter |
| `cloud_provider` |  |  | Filter results by their provider |


**GET - CloudCredential**

Create cloud credential

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `Payload` |  | ✓ | POST method's JSON data |


### /cloud_credential/{cloud_credential_id}

**GET - CloudCredential**

Get cloud credential

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `cloud_credential_id` |  | ✓ | Cloud credential id |
| `full` |  |  | If set to true, resolves all urls to actual objects |


**GET - CloudCredential**

Update cloud credential

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `cloud_credential_id` |  | ✓ | Cloud credential id |
| `Payload` |  | ✓ | PUT method's JSON data |


### /cloud_credential/{cloud_credential_id}/cloud_discovery

**GET - CloudDiscovery**

Get cloud credential's cloud discoverys

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `cloud_credential_id` |  | ✓ | Cloud credential id |
| `full` |  |  | If set to true, resolves all urls to actual objects |
| `limit` |  |  | The number of returned items per page; set to 0 to get available data altogether (used for pagination) |
| `offset` |  |  | The beginning index of the item being returned in the list (used for pagination) |
| `order_by` |  |  | The name of the field to sort on; must be an integer, float, boolean, string, or date field |
| `order` |  |  | The sort order for the result set, specified in conjunction with the order_by parameter |


**GET - CloudDiscovery**

Create cloud credential's cloud discovery

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `cloud_credential_id` |  | ✓ | Cloud credential id |
| `Payload` |  | ✓ | POST method's JSON data |


### /cloud_credential/{cloud_credential_id}/cloud_discovery/{cloud_discovery_id}

**GET - CloudDiscovery**

Get cloud credential's cloud discovery

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `cloud_credential_id` |  | ✓ | Cloud credential id |
| `cloud_discovery_id` |  | ✓ | Cloud discovery id |
| `full` |  |  | If set to true, resolves all urls to actual objects |


**GET - CloudDiscovery**

Update cloud credential's cloud discovery

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `cloud_credential_id` |  | ✓ | Cloud credential id |
| `cloud_discovery_id` |  | ✓ | Cloud discovery id |
| `Payload` |  | ✓ | PUT method's JSON data |


### /cloud_credential/{cloud_credential_id}/run

**GET - RunDiscovery**

Run a discovery on the credential

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `cloud_credential_id` |  | ✓ | Cloud credential id |


---

<a name="cloud-provider"></a>
## cloud_provider

### /cloud_provider

**GET - CloudProvider**

Get cloud providers

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `full` |  |  | If set to true, resolves all urls to actual objects |
| `limit` |  |  | The number of returned items per page; set to 0 to get available data altogether (used for pagination) |
| `offset` |  |  | The beginning index of the item being returned in the list (used for pagination) |
| `order_by` |  |  | The name of the field to sort on; must be an integer, float, boolean, string, or date field |
| `order` |  |  | The sort order for the result set, specified in conjunction with the order_by parameter |


### /cloud_provider/{cloud_provider_id}

**GET - CloudProvider**

Get cloud provider

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `cloud_provider_id` |  | ✓ | Cloud provider id |
| `full` |  |  | If set to true, resolves all urls to actual objects |


---

<a name="cloud-region"></a>
## cloud_region

### /cloud_region

**GET - CloudRegion**

Get cloud regions

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `full` |  |  | If set to true, resolves all urls to actual objects |
| `limit` |  |  | The number of returned items per page; set to 0 to get available data altogether (used for pagination) |
| `offset` |  |  | The beginning index of the item being returned in the list (used for pagination) |
| `order_by` |  |  | The name of the field to sort on; must be an integer, float, boolean, string, or date field |
| `order` |  |  | The sort order for the result set, specified in conjunction with the order_by parameter |


### /cloud_region/{cloud_region_id}

**GET - CloudRegion**

Get cloud region

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `cloud_region_id` |  | ✓ | Cloud region id |
| `full` |  |  | If set to true, resolves all urls to actual objects |


---

<a name="cloud-service"></a>
## cloud_service

### /cloud_service

**GET - CloudService**

Get cloud services

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `full` |  |  | If set to true, resolves all urls to actual objects |
| `limit` |  |  | The number of returned items per page; set to 0 to get available data altogether (used for pagination) |
| `offset` |  |  | The beginning index of the item being returned in the list (used for pagination) |
| `order_by` |  |  | The name of the field to sort on; must be an integer, float, boolean, string, or date field |
| `order` |  |  | The sort order for the result set, specified in conjunction with the order_by parameter |


### /cloud_service/{cloud_service_id}

**GET - CloudService**

Get cloud service

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `cloud_service_id` |  | ✓ | Cloud service id |
| `full` |  |  | If set to true, resolves all urls to actual objects |


---

<a name="compound-service"></a>
## compound_service

### /compound_service

**GET - CompoundService**

Get compound services

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `full` |  |  | If set to true, resolves all urls to actual objects |
| `limit` |  |  | The number of returned items per page; set to 0 to get available data altogether (used for pagination) |
| `offset` |  |  | The beginning index of the item being returned in the list (used for pagination) |
| `order_by` |  |  | The name of the field to sort on; must be an integer, float, boolean, string, or date field |
| `order` |  |  | The sort order for the result set, specified in conjunction with the order_by parameter |
| `name` |  |  | Filter results by name |
| `tags` |  |  | Filter results by tags (comma separated) |


**GET - CompoundService**

Create compound service

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `Payload` |  | ✓ | POST method's JSON data |


### /compound_service/{compound_service_id}

**GET - CompoundService**

Get compound service

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `compound_service_id` |  | ✓ | Compound service id |
| `full` |  |  | If set to true, resolves all urls to actual objects |


**GET - CompoundService**

Update compound service

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `compound_service_id` |  | ✓ | Compound service id |
| `Payload` |  | ✓ | PUT method's JSON data |


**GET - CompoundService**

Delete compound service

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `compound_service_id` |  | ✓ | Compound service id |


### /compound_service/{compound_service_id}/agent_resource_threshold

**GET - AgentResourceThreshold**

Get compound service's agent resource thresholds

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `compound_service_id` |  | ✓ | Compound service id |
| `full` |  |  | If set to true, resolves all urls to actual objects |
| `limit` |  |  | The number of returned items per page; set to 0 to get available data altogether (used for pagination) |
| `offset` |  |  | The beginning index of the item being returned in the list (used for pagination) |
| `order_by` |  |  | The name of the field to sort on; must be an integer, float, boolean, string, or date field |
| `order` |  |  | The sort order for the result set, specified in conjunction with the order_by parameter |


### /compound_service/{compound_service_id}/agent_resource_threshold/{agent_resource_threshold_id}

**GET - AgentResourceThreshold**

Get compound service's agent resource threshold

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `compound_service_id` |  | ✓ | Compound service id |
| `agent_resource_threshold_id` |  | ✓ | Agent resource threshold id |
| `full` |  |  | If set to true, resolves all urls to actual objects |


### /compound_service/{compound_service_id}/availability

**GET - GetCompoundServiceAvailability**

Get compound service availability

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `compound_service_id` |  | ✓ | Compound service id |
| `full` |  |  | If set to true, resolves all urls to actual objects |
| `start_time` |  | ✓ | Start time of the range; format: YYYY-MM-DD HH:MM:SS |
| `end_time` |  | ✓ | End time of the range; format: YYYY-MM-DD HH:MM:SS |


### /compound_service/{compound_service_id}/network_service

**GET - NetworkService**

Get compound service's network services

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `compound_service_id` |  | ✓ | Compound service id |
| `full` |  |  | If set to true, resolves all urls to actual objects |
| `limit` |  |  | The number of returned items per page; set to 0 to get available data altogether (used for pagination) |
| `offset` |  |  | The beginning index of the item being returned in the list (used for pagination) |
| `order_by` |  |  | The name of the field to sort on; must be an integer, float, boolean, string, or date field |
| `order` |  |  | The sort order for the result set, specified in conjunction with the order_by parameter |
| `name` |  |  | Filter results by name |
| `service_type` |  |  | Filter results by service_type id |
| `server_interface` |  |  | Filter results by server_interface |
| `status` |  |  | Filter results by status |
| `tags` |  |  | Filter results by tags (comma separated) |
| `monitoring_location` |  |  | Filter results by monitoring location URL either server (https://api2.panopta.com/v2/server/{server_id}), appliance (https://api2.panopta.com/v2/onsight/{onsight_id}), or monitor node (https://api2.panopta.com/v2/monitoring_node/{monitoring_node_id}) |


### /compound_service/{compound_service_id}/network_service/{network_service_id}

**GET - NetworkService**

Get compound service's network service

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `compound_service_id` |  | ✓ | Compound service id |
| `network_service_id` |  | ✓ | Network service id |
| `full` |  |  | If set to true, resolves all urls to actual objects |


### /compound_service/{compound_service_id}/network_service/{network_service_id}/response_time/{timescale}

**GET - GetServiceResponseTimeGraphData**

Get service response time graph data

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `compound_service_id` |  | ✓ | Compound service id |
| `network_service_id` |  | ✓ | Network service id |
| `timescale` |  | ✓ | ('hour', 'day', 'week', 'month', or 'year') |
| `full` |  |  | If set to true, resolves all urls to actual objects |
| `end_time` |  |  | End time in UTC; format: YYYY-MM-DD HH:MM:SS |


### /compound_service/{compound_service_id}/outage

**GET - Outage**

Get compound service's outages

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `compound_service_id` |  | ✓ | Compound service id |
| `full` |  |  | If set to true, resolves all urls to actual objects |
| `limit` |  |  | The number of returned items per page; set to 0 to get available data altogether (used for pagination) |
| `offset` |  |  | The beginning index of the item being returned in the list (used for pagination) |
| `order_by` |  |  | The name of the field to sort on; must be an integer, float, boolean, string, or date field |
| `order` |  |  | The sort order for the result set, specified in conjunction with the order_by parameter |
| `end_time` |  |  | End_time in UTC |
| `start_time` |  |  | Start_time in UTC |
| `status` |  |  |  |
| `min_duration` |  |  | Minimum outage duration in seconds |
| `order_by` |  |  | Default: -start_time |


---

<a name="contact"></a>
## contact

### /contact

**GET - Contact**

Get contacts

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `full` |  |  | If set to true, resolves all urls to actual objects |
| `limit` |  |  | The number of returned items per page; set to 0 to get available data altogether (used for pagination) |
| `offset` |  |  | The beginning index of the item being returned in the list (used for pagination) |
| `order_by` |  |  | The name of the field to sort on; must be an integer, float, boolean, string, or date field |
| `order` |  |  | The sort order for the result set, specified in conjunction with the order_by parameter |
| `name` |  |  | Filter results by name |


**GET - Contact**

Create contact

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `Payload` |  | ✓ | POST method's JSON data |


### /contact/{contact_id}

**GET - Contact**

Get contact

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `contact_id` |  | ✓ | Contact id |
| `full` |  |  | If set to true, resolves all urls to actual objects |


**GET - Contact**

Update contact

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `contact_id` |  | ✓ | Contact id |
| `Payload` |  | ✓ | PUT method's JSON data |


**GET - Contact**

Delete contact

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `contact_id` |  | ✓ | Contact id |


### /contact/{contact_id}/contact_info

**GET - ContactInfo**

Get contact's contact infos

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `contact_id` |  | ✓ | Contact id |
| `full` |  |  | If set to true, resolves all urls to actual objects |
| `limit` |  |  | The number of returned items per page; set to 0 to get available data altogether (used for pagination) |
| `offset` |  |  | The beginning index of the item being returned in the list (used for pagination) |
| `order_by` |  |  | The name of the field to sort on; must be an integer, float, boolean, string, or date field |
| `order` |  |  | The sort order for the result set, specified in conjunction with the order_by parameter |


**GET - ContactInfo**

Create contact's contact info

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `contact_id` |  | ✓ | Contact id |
| `Payload` |  | ✓ | POST method's JSON data |


### /contact/{contact_id}/contact_info/{contact_info_id}

**GET - ContactInfo**

Get contact's contact info

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `contact_id` |  | ✓ | Contact id |
| `contact_info_id` |  | ✓ | Contact info id |
| `full` |  |  | If set to true, resolves all urls to actual objects |


**GET - ContactInfo**

Update contact's contact info

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `contact_id` |  | ✓ | Contact id |
| `contact_info_id` |  | ✓ | Contact info id |
| `Payload` |  | ✓ | PUT method's JSON data |


**GET - ContactInfo**

Delete contact's contact info

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `contact_id` |  | ✓ | Contact id |
| `contact_info_id` |  | ✓ | Contact info id |


**GET - ContactInfo**

Create contact's contact info

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `contact_id` |  | ✓ | Contact id |
| `contact_info_id` |  | ✓ | Contact info id |
| `Payload` |  | ✓ | POST method's JSON data |


---

<a name="contact-group"></a>
## contact_group

### /contact_group

**GET - ContactGroup**

Get contact groups

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `full` |  |  | If set to true, resolves all urls to actual objects |
| `limit` |  |  | The number of returned items per page; set to 0 to get available data altogether (used for pagination) |
| `offset` |  |  | The beginning index of the item being returned in the list (used for pagination) |
| `order_by` |  |  | The name of the field to sort on; must be an integer, float, boolean, string, or date field |
| `order` |  |  | The sort order for the result set, specified in conjunction with the order_by parameter |


**GET - ContactGroup**

Create contact group

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `Payload` |  | ✓ | POST method's JSON data |


### /contact_group/{contact_group_id}

**GET - ContactGroup**

Get contact group

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `contact_group_id` |  | ✓ | Contact group id |
| `full` |  |  | If set to true, resolves all urls to actual objects |


**GET - ContactGroup**

Update contact group

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `contact_group_id` |  | ✓ | Contact group id |
| `Payload` |  | ✓ | PUT method's JSON data |


**GET - ContactGroup**

Delete contact group

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `contact_group_id` |  | ✓ | Contact group id |


---

<a name="contact-type"></a>
## contact_type

### /contact_type

**GET - ContactType**

Get contact types

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `full` |  |  | If set to true, resolves all urls to actual objects |
| `limit` |  |  | The number of returned items per page; set to 0 to get available data altogether (used for pagination) |
| `offset` |  |  | The beginning index of the item being returned in the list (used for pagination) |
| `order_by` |  |  | The name of the field to sort on; must be an integer, float, boolean, string, or date field |
| `order` |  |  | The sort order for the result set, specified in conjunction with the order_by parameter |
| `name` |  |  | Filter results by name |


### /contact_type/{contact_type_id}

**GET - ContactType**

Get contact type

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `contact_type_id` |  | ✓ | Contact type id |
| `full` |  |  | If set to true, resolves all urls to actual objects |


---

<a name="dashboard"></a>
## dashboard

### /dashboard

**GET - Dashboard**

Get dashboards

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `full` |  |  | If set to true, resolves all urls to actual objects |
| `limit` |  |  | The number of returned items per page; set to 0 to get available data altogether (used for pagination) |
| `offset` |  |  | The beginning index of the item being returned in the list (used for pagination) |
| `order_by` |  |  | The name of the field to sort on; must be an integer, float, boolean, string, or date field |
| `order` |  |  | The sort order for the result set, specified in conjunction with the order_by parameter |


**GET - Dashboard**

Create dashboard

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `Payload` |  | ✓ | POST method's JSON data |


### /dashboard/{dashboard_id}

**GET - Dashboard**

Get dashboard

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `dashboard_id` |  | ✓ | Dashboard id |
| `full` |  |  | If set to true, resolves all urls to actual objects |


**GET - Dashboard**

Update dashboard

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `dashboard_id` |  | ✓ | Dashboard id |
| `Payload` |  | ✓ | PUT method's JSON data |


**GET - Dashboard**

Delete dashboard

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `dashboard_id` |  | ✓ | Dashboard id |


---

<a name="dem-application"></a>
## dem_application

### /dem_application

**GET - DemApplication**

Get dem applications

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `full` |  |  | If set to true, resolves all urls to actual objects |
| `limit` |  |  | The number of returned items per page; set to 0 to get available data altogether (used for pagination) |
| `offset` |  |  | The beginning index of the item being returned in the list (used for pagination) |
| `order_by` |  |  | The name of the field to sort on; must be an integer, float, boolean, string, or date field |
| `order` |  |  | The sort order for the result set, specified in conjunction with the order_by parameter |


**GET - DemApplication**

Create dem application

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `Payload` |  | ✓ | POST method's JSON data |


### /dem_application/{dem_application_id}

**GET - DemApplication**

Get dem application

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `dem_application_id` |  | ✓ | Dem application id |
| `full` |  |  | If set to true, resolves all urls to actual objects |


**GET - DemApplication**

Update dem application

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `dem_application_id` |  | ✓ | Dem application id |
| `Payload` |  | ✓ | PUT method's JSON data |


**GET - DemApplication**

Delete dem application

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `dem_application_id` |  | ✓ | Dem application id |


### /dem_application/{dem_application_id}/instance

**GET - AddDemTemplateInstance**

Add dem template instance

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `dem_application_id` |  | ✓ | Dem application id |
| `full` |  |  | If set to true, resolves all urls to actual objects |
| `limit` |  |  | The number of returned items per page; set to 0 to get available data altogether (used for pagination) |
| `offset` |  |  | The beginning index of the item being returned in the list (used for pagination) |
| `order_by` |  |  | The name of the field to sort on; must be an integer, float, boolean, string, or date field |
| `order` |  |  | The sort order for the result set, specified in conjunction with the order_by parameter |
| `fqdn` |  |  | Fqdn of the template, should not be empty |
| `name` |  |  | Name of the template, should not be empty |
| `tags` |  |  | Tags of the template instance |
| `notification_schedule` |  |  | URL to a NotificationSchedule that will be used for the application; Url format = https://api2.panopta.com/v2/notification_schedule/{notification_schedule_id} |


**GET - AddDemTemplateInstance**

Add dem template instance

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `dem_application_id` |  | ✓ | Dem application id |
| `Payload` |  | ✓ | POST method's JSON data |


### /dem_application/{dem_application_id}/instance/{server_template_id}/path_monitoring

**GET - SetPathMonitoring**

Set path monitoring

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `dem_application_id` |  | ✓ | Dem application id |
| `server_template_id` |  | ✓ | Server template id |
| `Payload` |  | ✓ | PUT method's JSON data |


### /dem_application/{dem_application_id}/location

**GET - DemMonitoringLocation**

Dem monitoring location

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `dem_application_id` |  | ✓ | Dem application id |
| `full` |  |  | If set to true, resolves all urls to actual objects |
| `limit` |  |  | The number of returned items per page; set to 0 to get available data altogether (used for pagination) |
| `offset` |  |  | The beginning index of the item being returned in the list (used for pagination) |
| `order_by` |  |  | The name of the field to sort on; must be an integer, float, boolean, string, or date field |
| `order` |  |  | The sort order for the result set, specified in conjunction with the order_by parameter |
| `endpoint_agent` |  |  |  Url format = https://api2.panopta.com/v2/server/{server_id} |
| `public_probes` |  |  |  Url format = https://api2.panopta.com/v2/monitoring_node/{monitoring_node_id} |
| `onsight` |  |  |  Url format = https://api2.panopta.com/v2/onsight/{onsight_id} |
| `sdwan_device` |  |  |  Url format = https://api2.panopta.com/v2/server/{server_id} |
| `add_replace` |  |  | Pass 'add' as an option to either add the monitoring location(s) or pass 'replace' to completely replace the existing monitoring location(s). This might take effect in a few minutes. If nothing is passed, 'add' will be used as a default. |
| `type_filter` |  |  | Filter GET results by monitoring location type |


**GET - DemMonitoringLocation**

Dem monitoring location

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `dem_application_id` |  | ✓ | Dem application id |
| `Payload` |  | ✓ | PUT method's JSON data |


---

<a name="fabric-connection"></a>
## fabric_connection

### /fabric_connection

**GET - FabricConnection**

Get fabric connections

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `full` |  |  | If set to true, resolves all urls to actual objects |
| `limit` |  |  | The number of returned items per page; set to 0 to get available data altogether (used for pagination) |
| `offset` |  |  | The beginning index of the item being returned in the list (used for pagination) |
| `order_by` |  |  | The name of the field to sort on; must be an integer, float, boolean, string, or date field |
| `order` |  |  | The sort order for the result set, specified in conjunction with the order_by parameter |
| `status` |  |  | Filter results by status |


**GET - FabricConnection**

Create fabric connection

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `Payload` |  | ✓ | POST method's JSON data |


### /fabric_connection/{fabric_connection_id}

**GET - FabricConnection**

Get fabric connection

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `fabric_connection_id` |  | ✓ | Fabric connection id |
| `full` |  |  | If set to true, resolves all urls to actual objects |


**GET - FabricConnection**

Delete fabric connection

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `fabric_connection_id` |  | ✓ | Fabric connection id |


---

<a name="historical-outage"></a>
## historical_outage

### /historical_outage

**GET - HistoricalOutage**

Create historical outage

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `Payload` |  | ✓ | POST method's JSON data |


### /historical_outage/{historical_outage_id}

---

<a name="maintenance-schedule"></a>
## maintenance_schedule

### /maintenance_schedule

**GET - MaintenanceSchedule**

Get maintenance schedules

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `full` |  |  | If set to true, resolves all urls to actual objects |
| `limit` |  |  | The number of returned items per page; set to 0 to get available data altogether (used for pagination) |
| `offset` |  |  | The beginning index of the item being returned in the list (used for pagination) |
| `order_by` |  |  | The name of the field to sort on; must be an integer, float, boolean, string, or date field |
| `order` |  |  | The sort order for the result set, specified in conjunction with the order_by parameter |
| `name` |  |  | Filter results by name |


**GET - MaintenanceSchedule**

Create maintenance schedule

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `Payload` |  | ✓ | POST method's JSON data |


### /maintenance_schedule/active

**GET - GetActiveMaintenanceSchedules**

Get active maintenance schedules

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `full` |  |  | If set to true, resolves all urls to actual objects |
| `limit` |  |  | The number of returned items per page; set to 0 to get available data altogether (used for pagination) |
| `offset` |  |  | The beginning index of the item being returned in the list (used for pagination) |
| `order_by` |  |  | The name of the field to sort on; must be an integer, float, boolean, string, or date field |
| `order` |  |  | The sort order for the result set, specified in conjunction with the order_by parameter |


### /maintenance_schedule/active_or_pending

**GET - GetActiveOrPendingMaintenanceSchedules**

Get active or pending maintenance schedules

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `full` |  |  | If set to true, resolves all urls to actual objects |
| `limit` |  |  | The number of returned items per page; set to 0 to get available data altogether (used for pagination) |
| `offset` |  |  | The beginning index of the item being returned in the list (used for pagination) |
| `order_by` |  |  | The name of the field to sort on; must be an integer, float, boolean, string, or date field |
| `order` |  |  | The sort order for the result set, specified in conjunction with the order_by parameter |


### /maintenance_schedule/{maintenance_schedule_id}

**GET - MaintenanceSchedule**

Get maintenance schedule

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `maintenance_schedule_id` |  | ✓ | Maintenance schedule id |
| `full` |  |  | If set to true, resolves all urls to actual objects |


**GET - MaintenanceSchedule**

Update maintenance schedule

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `maintenance_schedule_id` |  | ✓ | Maintenance schedule id |
| `Payload` |  | ✓ | PUT method's JSON data |


**GET - MaintenanceSchedule**

Delete maintenance schedule

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `maintenance_schedule_id` |  | ✓ | Maintenance schedule id |


### /maintenance_schedule/{maintenance_schedule_id}/extend/{num_minutes}

**GET - ExtendMaintenanceSchedule**

Extend maintenance schedule

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `maintenance_schedule_id` |  | ✓ | Maintenance schedule id |
| `num_minutes` |  | ✓ | Num minutes |
| `Payload` |  | ✓ | PUT method's JSON data |


### /maintenance_schedule/{maintenance_schedule_id}/pause

**GET - PauseMaintenanceSchedule**

Pause maintenance schedule

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `maintenance_schedule_id` |  | ✓ | Maintenance schedule id |
| `Payload` |  | ✓ | PUT method's JSON data |


### /maintenance_schedule/{maintenance_schedule_id}/resume

**GET - ResumeMaintenanceSchedule**

Resume maintenance schedule

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `maintenance_schedule_id` |  | ✓ | Maintenance schedule id |
| `Payload` |  | ✓ | PUT method's JSON data |


### /maintenance_schedule/{maintenance_schedule_id}/terminate

**GET - TerminateMaintenanceSchedule**

Terminate maintenance schedule

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `maintenance_schedule_id` |  | ✓ | Maintenance schedule id |
| `Payload` |  | ✓ | PUT method's JSON data |


---

<a name="monitoring-node"></a>
## monitoring_node

### /monitoring_node

**GET - MonitoringNode**

Get monitoring nodes

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `full` |  |  | If set to true, resolves all urls to actual objects |
| `limit` |  |  | The number of returned items per page; set to 0 to get available data altogether (used for pagination) |
| `offset` |  |  | The beginning index of the item being returned in the list (used for pagination) |
| `order_by` |  |  | The name of the field to sort on; must be an integer, float, boolean, string, or date field |
| `order` |  |  | The sort order for the result set, specified in conjunction with the order_by parameter |
| `name` |  |  | Filter results by name |
| `hostname` |  |  | Filter results by hostname |
| `ip_address` |  |  | Filter results by ip_address |


### /monitoring_node/{monitoring_node_id}

**GET - MonitoringNode**

Get monitoring node

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `monitoring_node_id` |  | ✓ | Monitoring node id |
| `full` |  |  | If set to true, resolves all urls to actual objects |


---

<a name="network-service-type"></a>
## network_service_type

### /network_service_type

**GET - NetworkServiceType**

Get network service types

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `full` |  |  | If set to true, resolves all urls to actual objects |
| `limit` |  |  | The number of returned items per page; set to 0 to get available data altogether (used for pagination) |
| `offset` |  |  | The beginning index of the item being returned in the list (used for pagination) |
| `order_by` |  |  | The name of the field to sort on; must be an integer, float, boolean, string, or date field |
| `order` |  |  | The sort order for the result set, specified in conjunction with the order_by parameter |
| `name` |  |  | Filter results by name |
| `textkey` |  |  | Filter results by textkey |
| `service_class` |  |  | Filter results by service_class |


### /network_service_type/{network_service_type_id}

**GET - NetworkServiceType**

Get network service type

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `network_service_type_id` |  | ✓ | Network service type id |
| `full` |  |  | If set to true, resolves all urls to actual objects |


### /network_service_type/{network_service_type_id}/option/{option_id}

**GET - Option**

Get network service type's option

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `network_service_type_id` |  | ✓ | Network service type id |
| `option_id` |  | ✓ | Option id |
| `full` |  |  | If set to true, resolves all urls to actual objects |


---

<a name="notification-schedule"></a>
## notification_schedule

### /notification_schedule

**GET - NotificationSchedule**

Get notification schedules

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `full` |  |  | If set to true, resolves all urls to actual objects |
| `limit` |  |  | The number of returned items per page; set to 0 to get available data altogether (used for pagination) |
| `offset` |  |  | The beginning index of the item being returned in the list (used for pagination) |
| `order_by` |  |  | The name of the field to sort on; must be an integer, float, boolean, string, or date field |
| `order` |  |  | The sort order for the result set, specified in conjunction with the order_by parameter |
| `name` |  |  | Filter results by name |


**GET - NotificationSchedule**

Create notification schedule

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `Payload` |  | ✓ | POST method's JSON data |


### /notification_schedule/{notification_schedule_id}

**GET - NotificationSchedule**

Get notification schedule

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `notification_schedule_id` |  | ✓ | Notification schedule id |
| `full` |  |  | If set to true, resolves all urls to actual objects |


**GET - NotificationSchedule**

Update notification schedule

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `notification_schedule_id` |  | ✓ | Notification schedule id |
| `Payload` |  | ✓ | PUT method's JSON data |


**GET - NotificationSchedule**

Delete notification schedule

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `notification_schedule_id` |  | ✓ | Notification schedule id |


### /notification_schedule/{notification_schedule_id}/agent_resource_threshold

**GET - AgentResourceThreshold**

Get notification schedule's agent resource thresholds

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `notification_schedule_id` |  | ✓ | Notification schedule id |
| `full` |  |  | If set to true, resolves all urls to actual objects |
| `limit` |  |  | The number of returned items per page; set to 0 to get available data altogether (used for pagination) |
| `offset` |  |  | The beginning index of the item being returned in the list (used for pagination) |
| `order_by` |  |  | The name of the field to sort on; must be an integer, float, boolean, string, or date field |
| `order` |  |  | The sort order for the result set, specified in conjunction with the order_by parameter |


### /notification_schedule/{notification_schedule_id}/compound_service

**GET - CompoundService**

Get notification schedule's compound services

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `notification_schedule_id` |  | ✓ | Notification schedule id |
| `full` |  |  | If set to true, resolves all urls to actual objects |
| `limit` |  |  | The number of returned items per page; set to 0 to get available data altogether (used for pagination) |
| `offset` |  |  | The beginning index of the item being returned in the list (used for pagination) |
| `order_by` |  |  | The name of the field to sort on; must be an integer, float, boolean, string, or date field |
| `order` |  |  | The sort order for the result set, specified in conjunction with the order_by parameter |
| `name` |  |  | Filter results by name |
| `tags` |  |  | Filter results by tags (comma separated) |


### /notification_schedule/{notification_schedule_id}/network_service

**GET - NetworkService**

Get notification schedule's network services

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `notification_schedule_id` |  | ✓ | Notification schedule id |
| `full` |  |  | If set to true, resolves all urls to actual objects |
| `limit` |  |  | The number of returned items per page; set to 0 to get available data altogether (used for pagination) |
| `offset` |  |  | The beginning index of the item being returned in the list (used for pagination) |
| `order_by` |  |  | The name of the field to sort on; must be an integer, float, boolean, string, or date field |
| `order` |  |  | The sort order for the result set, specified in conjunction with the order_by parameter |
| `name` |  |  | Filter results by name |
| `service_type` |  |  | Filter results by service_type id |
| `server_interface` |  |  | Filter results by server_interface |
| `status` |  |  | Filter results by status |
| `tags` |  |  | Filter results by tags (comma separated) |
| `monitoring_location` |  |  | Filter results by monitoring location URL either server (https://api2.panopta.com/v2/server/{server_id}), appliance (https://api2.panopta.com/v2/onsight/{onsight_id}), or monitor node (https://api2.panopta.com/v2/monitoring_node/{monitoring_node_id}) |


### /notification_schedule/{notification_schedule_id}/server

**GET - Server**

Get notification schedule's servers

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `notification_schedule_id` |  | ✓ | Notification schedule id |
| `full` |  |  | If set to true, resolves all urls to actual objects |
| `limit` |  |  | The number of returned items per page; set to 0 to get available data altogether (used for pagination) |
| `offset` |  |  | The beginning index of the item being returned in the list (used for pagination) |
| `order_by` |  |  | The name of the field to sort on; must be an integer, float, boolean, string, or date field |
| `order` |  |  | The sort order for the result set, specified in conjunction with the order_by parameter |
| `name` |  |  | Filter results by name |
| `fqdn` |  |  | Filter results by fqdn |
| `server_key` |  |  | Filter results by server_key |
| `partner_server_id` |  |  | Filter results by partner_server_id |
| `tags` |  |  | Filter results by tags (comma separated) |
| `attributes` |  |  | Filter results by attribute {name:value} pairs (comma separated) |
| `server_group` |  |  | Filter results by server_group id |
| `status` |  |  | Filter results by status |


### /notification_schedule/{notification_schedule_id}/server_group

**GET - ServerGroup**

Get notification schedule's server groups

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `notification_schedule_id` |  | ✓ | Notification schedule id |
| `full` |  |  | If set to true, resolves all urls to actual objects |
| `limit` |  |  | The number of returned items per page; set to 0 to get available data altogether (used for pagination) |
| `offset` |  |  | The beginning index of the item being returned in the list (used for pagination) |
| `order_by` |  |  | The name of the field to sort on; must be an integer, float, boolean, string, or date field |
| `order` |  |  | The sort order for the result set, specified in conjunction with the order_by parameter |
| `name` |  |  | Filter results by name |
| `tags` |  |  | Filter results by tags (comma separated) |
| `root_only` |  |  |  |


---

<a name="onsight"></a>
## onsight

### /onsight

**GET - Onsight**

Get onsights

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `full` |  |  | If set to true, resolves all urls to actual objects |
| `limit` |  |  | The number of returned items per page; set to 0 to get available data altogether (used for pagination) |
| `offset` |  |  | The beginning index of the item being returned in the list (used for pagination) |
| `order_by` |  |  | The name of the field to sort on; must be an integer, float, boolean, string, or date field |
| `order` |  |  | The sort order for the result set, specified in conjunction with the order_by parameter |
| `name` |  |  | Filter results by name |


**GET - Onsight**

Create onsight

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `Payload` |  | ✓ | POST method's JSON data |


### /onsight/{onsight_id}

**GET - Onsight**

Get onsight

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `onsight_id` |  | ✓ | Onsight id |
| `full` |  |  | If set to true, resolves all urls to actual objects |


**GET - Onsight**

Update onsight

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `onsight_id` |  | ✓ | Onsight id |
| `Payload` |  | ✓ | PUT method's JSON data |


**GET - Onsight**

Delete onsight

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `onsight_id` |  | ✓ | Onsight id |


### /onsight/{onsight_id}/countermeasure_metadata

**GET - CountermeasureMetadata**

Get onsight's countermeasure metadatas

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `onsight_id` |  | ✓ | Onsight id |
| `full` |  |  | If set to true, resolves all urls to actual objects |
| `limit` |  |  | The number of returned items per page; set to 0 to get available data altogether (used for pagination) |
| `offset` |  |  | The beginning index of the item being returned in the list (used for pagination) |
| `order_by` |  |  | The name of the field to sort on; must be an integer, float, boolean, string, or date field |
| `order` |  |  | The sort order for the result set, specified in conjunction with the order_by parameter |
| `status` |  |  | Filter results by status |


### /onsight/{onsight_id}/countermeasure_metadata/{countermeasure_metadata_id}

**GET - CountermeasureMetadata**

Get onsight's countermeasure metadata

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `onsight_id` |  | ✓ | Onsight id |
| `countermeasure_metadata_id` |  | ✓ | Countermeasure metadata id |
| `full` |  |  | If set to true, resolves all urls to actual objects |


### /onsight/{onsight_id}/servers

**GET - GetDiscoveredServers**

OnSight discovered servers

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `onsight_id` |  | ✓ | Onsight id |
| `full` |  |  | If set to true, resolves all urls to actual objects |


---

<a name="onsight-group"></a>
## onsight_group

### /onsight_group

**GET - OnsightGroup**

Get onsight groups

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `full` |  |  | If set to true, resolves all urls to actual objects |
| `limit` |  |  | The number of returned items per page; set to 0 to get available data altogether (used for pagination) |
| `offset` |  |  | The beginning index of the item being returned in the list (used for pagination) |
| `order_by` |  |  | The name of the field to sort on; must be an integer, float, boolean, string, or date field |
| `order` |  |  | The sort order for the result set, specified in conjunction with the order_by parameter |
| `name` |  |  | Filter results by name |


**GET - OnsightGroup**

Create onsight group

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `Payload` |  | ✓ | POST method's JSON data |


### /onsight_group/{onsight_group_id}

**GET - OnsightGroup**

Get onsight group

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `onsight_group_id` |  | ✓ | Onsight group id |
| `full` |  |  | If set to true, resolves all urls to actual objects |


**GET - OnsightGroup**

Update onsight group

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `onsight_group_id` |  | ✓ | Onsight group id |
| `Payload` |  | ✓ | PUT method's JSON data |


**GET - OnsightGroup**

Delete onsight group

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `onsight_group_id` |  | ✓ | Onsight group id |


---

<a name="outage"></a>
## outage

### /outage

**GET - Outage**

Get outages

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `full` |  |  | If set to true, resolves all urls to actual objects |
| `limit` |  |  | The number of returned items per page; set to 0 to get available data altogether (used for pagination) |
| `offset` |  |  | The beginning index of the item being returned in the list (used for pagination) |
| `order_by` |  |  | The name of the field to sort on; must be an integer, float, boolean, string, or date field |
| `order` |  |  | The sort order for the result set, specified in conjunction with the order_by parameter |
| `server` |  |  | Filter results by server id |
| `severity` |  |  | Filter results by severity |
| `status` |  |  | Filter results by status |
| `end_time` |  |  | End_time in UTC |
| `start_time` |  |  | Start_time in UTC |


### /outage/active

**GET - GetActiveOutages**

Get active outages

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `full` |  |  | If set to true, resolves all urls to actual objects |
| `limit` |  |  | The number of returned items per page; set to 0 to get available data altogether (used for pagination) |
| `offset` |  |  | The beginning index of the item being returned in the list (used for pagination) |
| `order_by` |  |  | The name of the field to sort on; must be an integer, float, boolean, string, or date field |
| `order` |  |  | The sort order for the result set, specified in conjunction with the order_by parameter |
| `server_id` |  |  | Filter active outages by server id. |


### /outage/resolved

**GET - GetResolvedOutages**

Get resolved outages

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `full` |  |  | If set to true, resolves all urls to actual objects |
| `limit` |  |  | The number of returned items per page; set to 0 to get available data altogether (used for pagination) |
| `offset` |  |  | The beginning index of the item being returned in the list (used for pagination) |
| `order_by` |  |  | The name of the field to sort on; must be an integer, float, boolean, string, or date field |
| `order` |  |  | The sort order for the result set, specified in conjunction with the order_by parameter |
| `end_time` |  |  | End time of the range in UTC |
| `start_time` |  |  | Start time of the range in UTC |
| `min_duration` |  |  | Minimum outage duration in seconds |
| `order_by` |  |  | Default: -start_time |


### /outage/{outage_id}

**GET - Outage**

Get outage

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `outage_id` |  | ✓ | Outage id |
| `full` |  |  | If set to true, resolves all urls to actual objects |
| `end_time` |  |  | End_time in UTC |
| `start_time` |  |  | Start_time in UTC |


### /outage/{outage_id}/acknowledge

**GET - HandleAcknowledge**

Acknowledge outage

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `outage_id` |  | ✓ | Outage id |
| `full` |  |  | If set to true, resolves all urls to actual objects |
| `who` |  | ✓ | Indicate who has acknowledged the alert; Url format = [https://api2.panopta.com/v2/user/{user_id} or https://api2.panopta.com/v2/contact/{contact_id}] |
| `delay_in_seconds` |  |  | Delay in seconds |
| `message` |  |  | Broadcast message |
| `should_broadcast` |  |  | Indicate that the message should be broadcasted |


**GET - HandleAcknowledge**

Acknowledge outage

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `outage_id` |  | ✓ | Outage id |
| `Payload` |  | ✓ | PUT method's JSON data |


### /outage/{outage_id}/actions

**GET - GetActions**

Notification actions

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `outage_id` |  | ✓ | Outage id |
| `full` |  |  | If set to true, resolves all urls to actual objects |


### /outage/{outage_id}/broadcast

**GET - BroadcastMessage**

Broadcast a message

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `outage_id` |  | ✓ | Outage id |
| `full` |  |  | If set to true, resolves all urls to actual objects |
| `who` |  | ✓ | Indicate who has boradcasted the alert message; Url format = [https://api2.panopta.com/v2/user/{user_id} or https://api2.panopta.com/v2/contact/{contact_id}] |
| `message` |  | ✓ | Broadcast message |


**GET - BroadcastMessage**

Broadcast a message

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `outage_id` |  | ✓ | Outage id |
| `Payload` |  | ✓ | PUT method's JSON data |


### /outage/{outage_id}/countermeasure

**GET - Countermeasure**

Get outage's countermeasures

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `outage_id` |  | ✓ | Outage id |
| `full` |  |  | If set to true, resolves all urls to actual objects |
| `limit` |  |  | The number of returned items per page; set to 0 to get available data altogether (used for pagination) |
| `offset` |  |  | The beginning index of the item being returned in the list (used for pagination) |
| `order_by` |  |  | The name of the field to sort on; must be an integer, float, boolean, string, or date field |
| `order` |  |  | The sort order for the result set, specified in conjunction with the order_by parameter |
| `status` |  |  | Filter results by status |


**GET - Countermeasure**

Update outage's countermeasure

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `outage_id` |  | ✓ | Outage id |
| `Payload` |  | ✓ | PUT method's JSON data |


### /outage/{outage_id}/countermeasure_metadata

**GET - GetCountermeasureMetadata**

Countermeasure metadata

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `outage_id` |  | ✓ | Outage id |
| `full` |  |  | If set to true, resolves all urls to actual objects |


### /outage/{outage_id}/countermeasure_output

**GET - GetCountermeasureOutput**

Countermeasure output

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `outage_id` |  | ✓ | Outage id |
| `full` |  |  | If set to true, resolves all urls to actual objects |


### /outage/{outage_id}/delay/{delay_in_seconds}

**GET - HandleEscalation**

Delay outage

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `outage_id` |  | ✓ | Outage id |
| `delay_in_seconds` |  | ✓ | Delay in seconds; a value of 0 meaning permanently delay any future alerts |
| `full` |  |  | If set to true, resolves all urls to actual objects |
| `who` |  | ✓ | Indicate who has acknowledged the alert; Url format = [https://api2.panopta.com/v2/user/{user_id} or https://api2.panopta.com/v2/contact/{contact_id}] |


**GET - HandleEscalation**

Delay outage

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `outage_id` |  | ✓ | Outage id |
| `delay_in_seconds` |  | ✓ | Delay in seconds; a value of 0 meaning permanently delay any future alerts |
| `Payload` |  | ✓ | PUT method's JSON data |


### /outage/{outage_id}/description

**GET - Update_description**

Update description of a custom incident

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `outage_id` |  | ✓ | Outage id |
| `Payload` |  | ✓ | PUT method's JSON data |


### /outage/{outage_id}/escalate

**GET - HandleEscalation**

Escalate outage

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `outage_id` |  | ✓ | Outage id |
| `full` |  |  | If set to true, resolves all urls to actual objects |
| `who` |  | ✓ | Indicate who has acknowledged the alert; Url format = [https://api2.panopta.com/v2/user/{user_id} or https://api2.panopta.com/v2/contact/{contact_id}] |


**GET - HandleEscalation**

Escalate outage

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `outage_id` |  | ✓ | Outage id |
| `Payload` |  | ✓ | PUT method's JSON data |


### /outage/{outage_id}/force_resolve

**GET - ForceResolve**

Force resolution of a manual incident

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `outage_id` |  | ✓ | Outage id |
| `Payload` |  | ✓ | PUT method's JSON data |


### /outage/{outage_id}/lead

**GET - HandleSetLead**

Lead on the outage

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `outage_id` |  | ✓ | Outage id |
| `Payload` |  | ✓ | PUT method's JSON data |


### /outage/{outage_id}/outage_log

**GET - OutageLog**

Get outage's outage logs

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `outage_id` |  | ✓ | Outage id |
| `full` |  |  | If set to true, resolves all urls to actual objects |
| `limit` |  |  | The number of returned items per page; set to 0 to get available data altogether (used for pagination) |
| `offset` |  |  | The beginning index of the item being returned in the list (used for pagination) |
| `order_by` |  |  | The name of the field to sort on; must be an integer, float, boolean, string, or date field |
| `order` |  |  | The sort order for the result set, specified in conjunction with the order_by parameter |
| `log_start_timestamp` |  |  | Log start timestamp in UTC; format: YYYY-MM-DD HH:MM:SS |


**GET - OutageLog**

Create outage's outage log

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `outage_id` |  | ✓ | Outage id |
| `log_start_timestamp` |  |  | Log start timestamp in UTC; format: YYYY-MM-DD HH:MM:SS |
| `Payload` |  | ✓ | POST method's JSON data |


### /outage/{outage_id}/outage_metadata

**GET - OutageMetadata**

Get outage's outage metadatas

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `outage_id` |  | ✓ | Outage id |
| `full` |  |  | If set to true, resolves all urls to actual objects |
| `limit` |  |  | The number of returned items per page; set to 0 to get available data altogether (used for pagination) |
| `offset` |  |  | The beginning index of the item being returned in the list (used for pagination) |
| `order_by` |  |  | The name of the field to sort on; must be an integer, float, boolean, string, or date field |
| `order` |  |  | The sort order for the result set, specified in conjunction with the order_by parameter |


**GET - OutageMetadata**

Create outage's outage metadata

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `outage_id` |  | ✓ | Outage id |
| `Payload` |  | ✓ | POST method's JSON data |


### /outage/{outage_id}/preoutage_graph

**GET - GetPreOutageGraphData**

Preoutage graph

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `outage_id` |  | ✓ | Outage id |
| `full` |  |  | If set to true, resolves all urls to actual objects |
| `timescale` |  |  | Graph timescale (defaults to hour) |


### /outage/{outage_id}/summary

**GET - OutageSummary**

Add a summary for your outage

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `outage_id` |  | ✓ | Outage id |
| `Payload` |  | ✓ | PUT method's JSON data |


### /outage/{outage_id}/tags

**GET - SaveTags**

Set tags for the incident

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `outage_id` |  | ✓ | Outage id |
| `Payload` |  | ✓ | PUT method's JSON data |


---

<a name="prometheus-resource"></a>
## prometheus_resource

### /prometheus_resource

**GET - PrometheusResource**

Create prometheus resource


---

<a name="public"></a>
## public

### /public/outage/{HASH}/acknowledge

**GET - AcknowledgeOutage**

Acknowledge outage

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `HASH` |  | ✓ | Outage hash |
| `full` |  |  | If set to true, resolves all urls to actual objects |
| `who` |  | ✓ | Indicate who has acknowledged the alert; Url format = [https://api2.panopta.com/v2/user/{user_id} or https://api2.panopta.com/v2/contact/{contact_id}] |


**GET - AcknowledgeOutage**

Acknowledge outage

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `HASH` |  | ✓ | Outage hash |
| `Payload` |  | ✓ | PUT method's JSON data |


### /public/outage/{HASH}/delay/{delay_in_seconds}

**GET - DelayOutage**

Delay outage

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `HASH` |  | ✓ | Outage hash |
| `delay_in_seconds` |  | ✓ | Delay in seconds; a value of 0 meaning permanently delay any future alerts |
| `full` |  |  | If set to true, resolves all urls to actual objects |
| `who` |  | ✓ | Indicate who has acknowledged the alert; Url format = [https://api2.panopta.com/v2/user/{user_id} or https://api2.panopta.com/v2/contact/{contact_id}] |


**GET - DelayOutage**

Delay outage

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `HASH` |  | ✓ | Outage hash |
| `delay_in_seconds` |  | ✓ | Delay in seconds; a value of 0 meaning permanently delay any future alerts |
| `Payload` |  | ✓ | PUT method's JSON data |


### /public/outage/{HASH}/escalate

**GET - EscalateOutage**

Escalate outage

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `HASH` |  | ✓ | Outage hash |
| `full` |  |  | If set to true, resolves all urls to actual objects |
| `who` |  | ✓ | Indicate who has acknowledged the alert; Url format = [https://api2.panopta.com/v2/user/{user_id} or https://api2.panopta.com/v2/contact/{contact_id}] |


**GET - EscalateOutage**

Escalate outage

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `HASH` |  | ✓ | Outage hash |
| `Payload` |  | ✓ | PUT method's JSON data |


---

<a name="role"></a>
## role

### /role

**GET - Role**

Get roles

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `full` |  |  | If set to true, resolves all urls to actual objects |
| `limit` |  |  | The number of returned items per page; set to 0 to get available data altogether (used for pagination) |
| `offset` |  |  | The beginning index of the item being returned in the list (used for pagination) |
| `order_by` |  |  | The name of the field to sort on; must be an integer, float, boolean, string, or date field |
| `order` |  |  | The sort order for the result set, specified in conjunction with the order_by parameter |


### /role/{role_id}

**GET - Role**

Get role

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `role_id` |  | ✓ | Role id |
| `full` |  |  | If set to true, resolves all urls to actual objects |


---

<a name="rotating-contact"></a>
## rotating_contact

### /rotating_contact

**GET - RotatingContact**

Get rotating contacts

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `full` |  |  | If set to true, resolves all urls to actual objects |
| `limit` |  |  | The number of returned items per page; set to 0 to get available data altogether (used for pagination) |
| `offset` |  |  | The beginning index of the item being returned in the list (used for pagination) |
| `order_by` |  |  | The name of the field to sort on; must be an integer, float, boolean, string, or date field |
| `order` |  |  | The sort order for the result set, specified in conjunction with the order_by parameter |
| `name` |  |  | Filter results by name |


**GET - RotatingContact**

Create rotating contact

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `Payload` |  | ✓ | POST method's JSON data |


### /rotating_contact/{rotating_contact_id}

**GET - RotatingContact**

Get rotating contact

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `rotating_contact_id` |  | ✓ | Rotating contact id |
| `full` |  |  | If set to true, resolves all urls to actual objects |


**GET - RotatingContact**

Update rotating contact

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `rotating_contact_id` |  | ✓ | Rotating contact id |
| `Payload` |  | ✓ | PUT method's JSON data |


**GET - RotatingContact**

Delete rotating contact

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `rotating_contact_id` |  | ✓ | Rotating contact id |


### /rotating_contact/{rotating_contact_id}/active

**GET - GetActiveContacts**

Get active contacts

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `rotating_contact_id` |  | ✓ | Rotating contact id |
| `full` |  |  | If set to true, resolves all urls to actual objects |
| `date` |  |  | Filters active contacts for a special date; format: YYYY-MM-DD |


---

<a name="server"></a>
## server

### /server

**GET - Server**

Get servers

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `full` |  |  | If set to true, resolves all urls to actual objects |
| `limit` |  |  | The number of returned items per page; set to 0 to get available data altogether (used for pagination) |
| `offset` |  |  | The beginning index of the item being returned in the list (used for pagination) |
| `order_by` |  |  | The name of the field to sort on; must be an integer, float, boolean, string, or date field |
| `order` |  |  | The sort order for the result set, specified in conjunction with the order_by parameter |
| `tag_filter_mode` |  |  | Mode in which to filter tags, choices: [or, and] |
| `attribute_filter_mode` |  |  | Mode in which to filter attributes, choices: [or, and] |
| `name` |  |  | Filter results by name |
| `fqdn` |  |  | Filter results by fqdn |
| `server_key` |  |  | Filter results by server_key |
| `partner_server_id` |  |  | Filter results by partner_server_id |
| `tags` |  |  | Filter results by tags (comma separated) |
| `attributes` |  |  | Filter results by attribute {name:value} pairs (comma separated) |
| `server_group` |  |  | Filter results by server_group id |
| `status` |  |  | Filter results by status |


**GET - Server**

Create server

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `Payload` |  | ✓ | POST method's JSON data |


### /server/request_report

**GET - RequestReport**

Request report

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `Payload` |  | ✓ | POST method's JSON data |


### /server/{server_id}

**GET - Server**

Get server

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `server_id` |  | ✓ | Server id |
| `full` |  |  | If set to true, resolves all urls to actual objects |


**GET - Server**

Update server

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `server_id` |  | ✓ | Server id |
| `Payload` |  | ✓ | PUT method's JSON data |


**GET - Server**

Delete server

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `server_id` |  | ✓ | Server id |


### /server/{server_id}/agent_resource

**GET - AgentResource**

Get server's agent resources

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `server_id` |  | ✓ | Server id |
| `full` |  |  | If set to true, resolves all urls to actual objects |
| `limit` |  |  | The number of returned items per page; set to 0 to get available data altogether (used for pagination) |
| `offset` |  |  | The beginning index of the item being returned in the list (used for pagination) |
| `order_by` |  |  | The name of the field to sort on; must be an integer, float, boolean, string, or date field |
| `order` |  |  | The sort order for the result set, specified in conjunction with the order_by parameter |
| `name` |  |  | Filter results by name |
| `tags` |  |  | Filter results by tags (comma separated) |
| `monitoring_location` |  |  | Filter results by monitoring location URL either server (https://api2.panopta.com/v2/server/{server_id}), appliance (https://api2.panopta.com/v2/onsight/{onsight_id}), or monitor node (https://api2.panopta.com/v2/monitoring_node/{monitoring_node_id}) |


**GET - AgentResource**

Create server's agent resource

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `server_id` |  | ✓ | Server id |
| `Payload` |  | ✓ | POST method's JSON data |


### /server/{server_id}/agent_resource/{agent_resource_id}

**GET - AgentResource**

Get server's agent resource

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `server_id` |  | ✓ | Server id |
| `agent_resource_id` |  | ✓ | Agent resource id |
| `full` |  |  | If set to true, resolves all urls to actual objects |


**GET - AgentResource**

Update server's agent resource

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `server_id` |  | ✓ | Server id |
| `agent_resource_id` |  | ✓ | Agent resource id |
| `Payload` |  | ✓ | PUT method's JSON data |


**GET - AgentResource**

Delete server's agent resource

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `server_id` |  | ✓ | Server id |
| `agent_resource_id` |  | ✓ | Agent resource id |


### /server/{server_id}/agent_resource/{agent_resource_id}/agent_resource_threshold/{agent_resource_threshold_id}

**GET - AgentResourceThreshold**

Get server's agent resource threshold

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `server_id` |  | ✓ | Server id |
| `agent_resource_id` |  | ✓ | Agent resource id |
| `agent_resource_threshold_id` |  | ✓ | Agent resource threshold id |
| `full` |  |  | If set to true, resolves all urls to actual objects |


**GET - AgentResourceThreshold**

Update server's agent resource threshold

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `server_id` |  | ✓ | Server id |
| `agent_resource_id` |  | ✓ | Agent resource id |
| `agent_resource_threshold_id` |  | ✓ | Agent resource threshold id |
| `Payload` |  | ✓ | PUT method's JSON data |


**GET - AgentResourceThreshold**

Delete server's agent resource threshold

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `server_id` |  | ✓ | Server id |
| `agent_resource_id` |  | ✓ | Agent resource id |
| `agent_resource_threshold_id` |  | ✓ | Agent resource threshold id |


### /server/{server_id}/agent_resource/{agent_resource_id}/agent_resource_threshold/{agent_resource_threshold_id}/countermeasure

**GET - AgentResourceThresholdCountermeasure**

Get server's agent resource threshold countermeasures

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `server_id` |  | ✓ | Server id |
| `agent_resource_id` |  | ✓ | Agent resource id |
| `agent_resource_threshold_id` |  | ✓ | Agent resource threshold id |
| `full` |  |  | If set to true, resolves all urls to actual objects |
| `limit` |  |  | The number of returned items per page; set to 0 to get available data altogether (used for pagination) |
| `offset` |  |  | The beginning index of the item being returned in the list (used for pagination) |
| `order_by` |  |  | The name of the field to sort on; must be an integer, float, boolean, string, or date field |
| `order` |  |  | The sort order for the result set, specified in conjunction with the order_by parameter |


**GET - AgentResourceThresholdCountermeasure**

Create server's agent resource threshold countermeasure

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `server_id` |  | ✓ | Server id |
| `agent_resource_id` |  | ✓ | Agent resource id |
| `agent_resource_threshold_id` |  | ✓ | Agent resource threshold id |
| `Payload` |  | ✓ | POST method's JSON data |


### /server/{server_id}/agent_resource/{agent_resource_id}/agent_resource_threshold/{agent_resource_threshold_id}/countermeasure/{agent_resource_threshold_countermeasure_id}

**GET - AgentResourceThresholdCountermeasure**

Get server's agent resource threshold countermeasure

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `server_id` |  | ✓ | Server id |
| `agent_resource_id` |  | ✓ | Agent resource id |
| `agent_resource_threshold_id` |  | ✓ | Agent resource threshold id |
| `agent_resource_threshold_countermeasure_id` |  | ✓ | Agent resource threshold countermeasure id |
| `full` |  |  | If set to true, resolves all urls to actual objects |


**GET - AgentResourceThresholdCountermeasure**

Update server's agent resource threshold countermeasure

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `server_id` |  | ✓ | Server id |
| `agent_resource_id` |  | ✓ | Agent resource id |
| `agent_resource_threshold_id` |  | ✓ | Agent resource threshold id |
| `agent_resource_threshold_countermeasure_id` |  | ✓ | Agent resource threshold countermeasure id |
| `Payload` |  | ✓ | PUT method's JSON data |


**GET - AgentResourceThresholdCountermeasure**

Delete server's agent resource threshold countermeasure

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `server_id` |  | ✓ | Server id |
| `agent_resource_id` |  | ✓ | Agent resource id |
| `agent_resource_threshold_id` |  | ✓ | Agent resource threshold id |
| `agent_resource_threshold_countermeasure_id` |  | ✓ | Agent resource threshold countermeasure id |


### /server/{server_id}/agent_resource/{agent_resource_id}/metric/{timescale}

**GET - GetAgentResourceMetricGraphData**

Get agent resource metric graph data

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `server_id` |  | ✓ | Server id |
| `agent_resource_id` |  | ✓ | Agent resource id |
| `timescale` |  | ✓ | ('hour', 'day', 'week', 'month', or 'year') |
| `full` |  |  | If set to true, resolves all urls to actual objects |
| `end_time` |  |  | End time in UTC; format: YYYY-MM-DD HH:MM:SS |
| `aggregate` |  |  | Whether to aggregate metric values into time slices |


### /server/{server_id}/apply_monitoring_policy

**GET - ApplyMonitoringPolicy**

Apply monitoring policy

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `server_id` |  | ✓ | Server id |


### /server/{server_id}/availability

**GET - GetServerAvailability**

Get server availability

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `server_id` |  | ✓ | Server id |
| `full` |  |  | If set to true, resolves all urls to actual objects |
| `start_time` |  | ✓ | Start time of the range; format: YYYY-MM-DD HH:MM:SS |
| `end_time` |  | ✓ | End time of the range; format: YYYY-MM-DD HH:MM:SS |
| `with_excluded_outages` |  |  | Include the outages that had been marked as excluded |


### /server/{server_id}/change_customer

**GET - ChangeCustomer**

Move server between customers

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `server_id` |  | ✓ | Server id |
| `Payload` |  | ✓ | PUT method's JSON data |


### /server/{server_id}/child_compound_service

**GET - CompoundService**

Get server's compound services

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `server_id` |  | ✓ | Server id |
| `full` |  |  | If set to true, resolves all urls to actual objects |
| `limit` |  |  | The number of returned items per page; set to 0 to get available data altogether (used for pagination) |
| `offset` |  |  | The beginning index of the item being returned in the list (used for pagination) |
| `order_by` |  |  | The name of the field to sort on; must be an integer, float, boolean, string, or date field |
| `order` |  |  | The sort order for the result set, specified in conjunction with the order_by parameter |
| `name` |  |  | Filter results by name |
| `tags` |  |  | Filter results by tags (comma separated) |


### /server/{server_id}/child_server

**GET - Server**

Get server's servers

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `server_id` |  | ✓ | Server id |
| `full` |  |  | If set to true, resolves all urls to actual objects |
| `limit` |  |  | The number of returned items per page; set to 0 to get available data altogether (used for pagination) |
| `offset` |  |  | The beginning index of the item being returned in the list (used for pagination) |
| `order_by` |  |  | The name of the field to sort on; must be an integer, float, boolean, string, or date field |
| `order` |  |  | The sort order for the result set, specified in conjunction with the order_by parameter |
| `name` |  |  | Filter results by name |
| `fqdn` |  |  | Filter results by fqdn |
| `server_key` |  |  | Filter results by server_key |
| `partner_server_id` |  |  | Filter results by partner_server_id |
| `tags` |  |  | Filter results by tags (comma separated) |
| `attributes` |  |  | Filter results by attribute {name:value} pairs (comma separated) |
| `server_group` |  |  | Filter results by server_group id |
| `status` |  |  | Filter results by status |


### /server/{server_id}/countermeasure_metadata

**GET - CountermeasureMetadata**

Get server's countermeasure metadatas

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `server_id` |  | ✓ | Server id |
| `full` |  |  | If set to true, resolves all urls to actual objects |
| `limit` |  |  | The number of returned items per page; set to 0 to get available data altogether (used for pagination) |
| `offset` |  |  | The beginning index of the item being returned in the list (used for pagination) |
| `order_by` |  |  | The name of the field to sort on; must be an integer, float, boolean, string, or date field |
| `order` |  |  | The sort order for the result set, specified in conjunction with the order_by parameter |
| `status` |  |  | Filter results by status |


### /server/{server_id}/countermeasure_metadata/{countermeasure_metadata_id}

**GET - CountermeasureMetadata**

Get server's countermeasure metadata

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `server_id` |  | ✓ | Server id |
| `countermeasure_metadata_id` |  | ✓ | Countermeasure metadata id |
| `full` |  |  | If set to true, resolves all urls to actual objects |


### /server/{server_id}/custom_incident

**GET - CreateCustomIncident**

Create custom incident

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `server_id` |  | ✓ | Server id |
| `Payload` |  | ✓ | POST method's JSON data |


### /server/{server_id}/fabric_resource/{fabric_resource_id}/metric/{timescale}

**GET - GetFabricResourceMetricGraphData**

Get fabric resource metric graph data

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `server_id` |  | ✓ | Server id |
| `fabric_resource_id` |  | ✓ | Fabric resource id |
| `timescale` |  | ✓ | ('hour', 'day', 'week', 'month', or 'year') |
| `full` |  |  | If set to true, resolves all urls to actual objects |
| `end_time` |  |  | End time in UTC; format: YYYY-MM-DD HH:MM:SS |
| `aggregate` |  |  | Whether to aggregate metric values into time slices |


### /server/{server_id}/flush_dns

**GET - FlushDNS**

Flush server DNS cache

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `server_id` |  | ✓ | Server id |
| `Payload` |  | ✓ | PUT method's JSON data |


### /server/{server_id}/maintenance_schedule

**GET - MaintenanceSchedule**

Get server's maintenance schedules

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `server_id` |  | ✓ | Server id |
| `full` |  |  | If set to true, resolves all urls to actual objects |
| `limit` |  |  | The number of returned items per page; set to 0 to get available data altogether (used for pagination) |
| `offset` |  |  | The beginning index of the item being returned in the list (used for pagination) |
| `order_by` |  |  | The name of the field to sort on; must be an integer, float, boolean, string, or date field |
| `order` |  |  | The sort order for the result set, specified in conjunction with the order_by parameter |
| `name` |  |  | Filter results by name |


### /server/{server_id}/network_service

**GET - NetworkService**

Get server's network services

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `server_id` |  | ✓ | Server id |
| `full` |  |  | If set to true, resolves all urls to actual objects |
| `limit` |  |  | The number of returned items per page; set to 0 to get available data altogether (used for pagination) |
| `offset` |  |  | The beginning index of the item being returned in the list (used for pagination) |
| `order_by` |  |  | The name of the field to sort on; must be an integer, float, boolean, string, or date field |
| `order` |  |  | The sort order for the result set, specified in conjunction with the order_by parameter |
| `ip_type` |  |  | Mode in which to filter by ip type, choices: [v4, v6] |
| `name` |  |  | Filter results by name |
| `service_type` |  |  | Filter results by service_type id |
| `server_interface` |  |  | Filter results by server_interface |
| `status` |  |  | Filter results by status |
| `tags` |  |  | Filter results by tags (comma separated) |
| `monitoring_location` |  |  | Filter results by monitoring location URL either server (https://api2.panopta.com/v2/server/{server_id}), appliance (https://api2.panopta.com/v2/onsight/{onsight_id}), or monitor node (https://api2.panopta.com/v2/monitoring_node/{monitoring_node_id}) |


**GET - NetworkService**

Create server's network service

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `server_id` |  | ✓ | Server id |
| `Payload` |  | ✓ | POST method's JSON data |


### /server/{server_id}/network_service/{network_service_id}

**GET - NetworkService**

Get server's network service

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `server_id` |  | ✓ | Server id |
| `network_service_id` |  | ✓ | Network service id |
| `full` |  |  | If set to true, resolves all urls to actual objects |


**GET - NetworkService**

Update server's network service

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `server_id` |  | ✓ | Server id |
| `network_service_id` |  | ✓ | Network service id |
| `Payload` |  | ✓ | PUT method's JSON data |


**GET - NetworkService**

Delete server's network service

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `server_id` |  | ✓ | Server id |
| `network_service_id` |  | ✓ | Network service id |


### /server/{server_id}/network_service/{network_service_id}/countermeasure

**GET - NetworkServiceCountermeasure**

Get server's network service countermeasures

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `server_id` |  | ✓ | Server id |
| `network_service_id` |  | ✓ | Network service id |
| `full` |  |  | If set to true, resolves all urls to actual objects |
| `limit` |  |  | The number of returned items per page; set to 0 to get available data altogether (used for pagination) |
| `offset` |  |  | The beginning index of the item being returned in the list (used for pagination) |
| `order_by` |  |  | The name of the field to sort on; must be an integer, float, boolean, string, or date field |
| `order` |  |  | The sort order for the result set, specified in conjunction with the order_by parameter |


**GET - NetworkServiceCountermeasure**

Create server's network service countermeasure

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `server_id` |  | ✓ | Server id |
| `network_service_id` |  | ✓ | Network service id |
| `Payload` |  | ✓ | POST method's JSON data |


### /server/{server_id}/network_service/{network_service_id}/countermeasure/{network_service_countermeasure_id}

**GET - NetworkServiceCountermeasure**

Get server's network service countermeasure

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `server_id` |  | ✓ | Server id |
| `network_service_id` |  | ✓ | Network service id |
| `network_service_countermeasure_id` |  | ✓ | Network service countermeasure id |
| `full` |  |  | If set to true, resolves all urls to actual objects |


**GET - NetworkServiceCountermeasure**

Update server's network service countermeasure

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `server_id` |  | ✓ | Server id |
| `network_service_id` |  | ✓ | Network service id |
| `network_service_countermeasure_id` |  | ✓ | Network service countermeasure id |
| `Payload` |  | ✓ | PUT method's JSON data |


**GET - NetworkServiceCountermeasure**

Delete server's network service countermeasure

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `server_id` |  | ✓ | Server id |
| `network_service_id` |  | ✓ | Network service id |
| `network_service_countermeasure_id` |  | ✓ | Network service countermeasure id |


### /server/{server_id}/network_service/{network_service_id}/response_time/{timescale}

**GET - GetServiceResponseTimeGraphData**

Get service response time graph data

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `server_id` |  | ✓ | Server id |
| `network_service_id` |  | ✓ | Network service id |
| `timescale` |  | ✓ | ('hour', 'day', 'week', 'month', or 'year') |
| `full` |  |  | If set to true, resolves all urls to actual objects |
| `end_time` |  |  | End time in UTC; format: YYYY-MM-DD HH:MM:SS |
| `aggregate` |  |  | Whether to aggregate metric values into time slices |


### /server/{server_id}/outage

**GET - Outage**

Get server's outages

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `server_id` |  | ✓ | Server id |
| `full` |  |  | If set to true, resolves all urls to actual objects |
| `limit` |  |  | The number of returned items per page; set to 0 to get available data altogether (used for pagination) |
| `offset` |  |  | The beginning index of the item being returned in the list (used for pagination) |
| `order_by` |  |  | The name of the field to sort on; must be an integer, float, boolean, string, or date field |
| `order` |  |  | The sort order for the result set, specified in conjunction with the order_by parameter |
| `server` |  |  | Filter results by server id |
| `severity` |  |  | Filter results by severity |
| `status` |  |  | Filter results by status |
| `end_time` |  |  | End_time in UTC |
| `start_time` |  |  | Start_time in UTC |


### /server/{server_id}/path_monitoring

**GET - PathMonitoring**

Get server's path monitorings

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `server_id` |  | ✓ | Server id |
| `full` |  |  | If set to true, resolves all urls to actual objects |
| `limit` |  |  | The number of returned items per page; set to 0 to get available data altogether (used for pagination) |
| `offset` |  |  | The beginning index of the item being returned in the list (used for pagination) |
| `order_by` |  |  | The name of the field to sort on; must be an integer, float, boolean, string, or date field |
| `order` |  |  | The sort order for the result set, specified in conjunction with the order_by parameter |
| `location` |  |  | Filter results by monitoring location URL either server (https://api2.panopta.com/v2/server/{server_id}), appliance (https://api2.panopta.com/v2/onsight/{onsight_id}), or monitor node (https://api2.panopta.com/v2/monitoring_node/{monitoring_node_id}) |


**GET - PathMonitoring**

Create server's path monitoring

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `server_id` |  | ✓ | Server id |
| `Payload` |  | ✓ | POST method's JSON data |


### /server/{server_id}/path_monitoring/{path_monitoring_id}

**GET - PathMonitoring**

Get server's path monitoring

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `server_id` |  | ✓ | Server id |
| `path_monitoring_id` |  | ✓ | Path monitoring id |
| `full` |  |  | If set to true, resolves all urls to actual objects |


**GET - PathMonitoring**

Delete server's path monitoring

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `server_id` |  | ✓ | Server id |
| `path_monitoring_id` |  | ✓ | Path monitoring id |


### /server/{server_id}/path_monitoring/{path_monitoring_id}/results

**GET - Get_path_monitoring_results**

Get path monitoring results

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `server_id` |  | ✓ | Server id |
| `path_monitoring_id` |  | ✓ | Path monitoring id |
| `full` |  |  | If set to true, resolves all urls to actual objects |
| `start_time` |  |  | Start time in UTC; format: YYYY-MM-DD HH:MM:SS |
| `end_time` |  |  | Start time in UTC; format: YYYY-MM-DD HH:MM:SS |


### /server/{server_id}/server_attribute

**GET - ServerAttribute**

Get server's server attributes

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `server_id` |  | ✓ | Server id |
| `full` |  |  | If set to true, resolves all urls to actual objects |
| `limit` |  |  | The number of returned items per page; set to 0 to get available data altogether (used for pagination) |
| `offset` |  |  | The beginning index of the item being returned in the list (used for pagination) |
| `order_by` |  |  | The name of the field to sort on; must be an integer, float, boolean, string, or date field |
| `order` |  |  | The sort order for the result set, specified in conjunction with the order_by parameter |


**GET - ServerAttribute**

Create server's server attribute

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `server_id` |  | ✓ | Server id |
| `Payload` |  | ✓ | POST method's JSON data |


### /server/{server_id}/server_attribute/{server_attribute_id}

**GET - ServerAttribute**

Get server's server attribute

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `server_id` |  | ✓ | Server id |
| `server_attribute_id` |  | ✓ | Server attribute id |
| `full` |  |  | If set to true, resolves all urls to actual objects |


**GET - ServerAttribute**

Delete server's server attribute

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `server_id` |  | ✓ | Server id |
| `server_attribute_id` |  | ✓ | Server attribute id |


### /server/{server_id}/server_log

**GET - ServerLog**

Get server's server logs

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `server_id` |  | ✓ | Server id |
| `full` |  |  | If set to true, resolves all urls to actual objects |
| `limit` |  |  | The number of returned items per page; set to 0 to get available data altogether (used for pagination) |
| `offset` |  |  | The beginning index of the item being returned in the list (used for pagination) |
| `order_by` |  |  | The name of the field to sort on; must be an integer, float, boolean, string, or date field |
| `order` |  |  | The sort order for the result set, specified in conjunction with the order_by parameter |


**GET - ServerLog**

Create server's server log

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `server_id` |  | ✓ | Server id |
| `Payload` |  | ✓ | POST method's JSON data |


### /server/{server_id}/server_resource_metadata

**GET - GetServerResourceMetadata**

Get server resource metadata

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `server_id` |  | ✓ | Server id |
| `full` |  |  | If set to true, resolves all urls to actual objects |
| `limit` |  |  | The number of returned items per page; set to 0 to get available data altogether (used for pagination) |
| `offset` |  |  | The beginning index of the item being returned in the list (used for pagination) |
| `order_by` |  |  | The name of the field to sort on; must be an integer, float, boolean, string, or date field |
| `order` |  |  | The sort order for the result set, specified in conjunction with the order_by parameter |


### /server/{server_id}/simulate_outage

**GET - SimulateOutage**

Simulate outage

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `server_id` |  | ✓ | Server id |
| `Payload` |  | ✓ | PUT method's JSON data |


### /server/{server_id}/snmp_discovery

**GET - RequestSNMPDiscovery**

Request SNMP discovery

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `server_id` |  | ✓ | Server id |
| `Payload` |  | ✓ | PUT method's JSON data |


### /server/{server_id}/snmp_resource

**GET - SnmpResource**

Get server's snmp resources

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `server_id` |  | ✓ | Server id |
| `full` |  |  | If set to true, resolves all urls to actual objects |
| `limit` |  |  | The number of returned items per page; set to 0 to get available data altogether (used for pagination) |
| `offset` |  |  | The beginning index of the item being returned in the list (used for pagination) |
| `order_by` |  |  | The name of the field to sort on; must be an integer, float, boolean, string, or date field |
| `order` |  |  | The sort order for the result set, specified in conjunction with the order_by parameter |
| `name` |  |  | Filter results by name |
| `base_oid` |  |  | Filter results by base_oid |
| `tags` |  |  | Filter results by tags (comma separated) |


**GET - SnmpResource**

Create server's snmp resource

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `server_id` |  | ✓ | Server id |
| `Payload` |  | ✓ | POST method's JSON data |


### /server/{server_id}/snmp_resource/{agent_resource_id}/agent_resource_threshold/{agent_resource_threshold_id}

**GET - AgentResourceThreshold**

Get server's agent resource threshold

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `server_id` |  | ✓ | Server id |
| `agent_resource_id` |  | ✓ | Agent resource id |
| `agent_resource_threshold_id` |  | ✓ | Agent resource threshold id |
| `full` |  |  | If set to true, resolves all urls to actual objects |


**GET - AgentResourceThreshold**

Update server's agent resource threshold

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `server_id` |  | ✓ | Server id |
| `agent_resource_id` |  | ✓ | Agent resource id |
| `agent_resource_threshold_id` |  | ✓ | Agent resource threshold id |
| `Payload` |  | ✓ | PUT method's JSON data |


**GET - AgentResourceThreshold**

Delete server's agent resource threshold

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `server_id` |  | ✓ | Server id |
| `agent_resource_id` |  | ✓ | Agent resource id |
| `agent_resource_threshold_id` |  | ✓ | Agent resource threshold id |


### /server/{server_id}/snmp_resource/{snmp_resource_id}

**GET - SnmpResource**

Get server's snmp resource

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `server_id` |  | ✓ | Server id |
| `snmp_resource_id` |  | ✓ | Snmp resource id |
| `full` |  |  | If set to true, resolves all urls to actual objects |


**GET - SnmpResource**

Update server's snmp resource

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `server_id` |  | ✓ | Server id |
| `snmp_resource_id` |  | ✓ | Snmp resource id |
| `Payload` |  | ✓ | PUT method's JSON data |


**GET - SnmpResource**

Delete server's snmp resource

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `server_id` |  | ✓ | Server id |
| `snmp_resource_id` |  | ✓ | Snmp resource id |


### /server/{server_id}/snmp_resource/{snmp_resource_id}/metric/{timescale}

**GET - GetSnmpResourceMetricGraphData**

Get snmp resource metric graph data

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `server_id` |  | ✓ | Server id |
| `snmp_resource_id` |  | ✓ | Snmp resource id |
| `timescale` |  | ✓ | ('hour', 'day', 'week', 'month', or 'year') |
| `full` |  |  | If set to true, resolves all urls to actual objects |
| `end_time` |  |  | End time in UTC; format: YYYY-MM-DD HH:MM:SS |
| `aggregate` |  |  | Whether to aggregate metric values into time slices |


### /server/{server_id}/template

**GET - ServerTemplate**

Get server's server templates

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `server_id` |  | ✓ | Server id |
| `full` |  |  | If set to true, resolves all urls to actual objects |
| `limit` |  |  | The number of returned items per page; set to 0 to get available data altogether (used for pagination) |
| `offset` |  |  | The beginning index of the item being returned in the list (used for pagination) |
| `order_by` |  |  | The name of the field to sort on; must be an integer, float, boolean, string, or date field |
| `order` |  |  | The sort order for the result set, specified in conjunction with the order_by parameter |


**GET - ServerTemplate**

Create server's server template

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `server_id` |  | ✓ | Server id |
| `Payload` |  | ✓ | POST method's JSON data |


### /server/{server_id}/template/{server_template_id}

**GET - ServerTemplate**

Delete server's server template

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `server_id` |  | ✓ | Server id |
| `server_template_id` |  | ✓ | Server template id |


---

<a name="server-attribute-type"></a>
## server_attribute_type

### /server_attribute_type

**GET - ServerAttributeType**

Get server attribute types

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `full` |  |  | If set to true, resolves all urls to actual objects |
| `limit` |  |  | The number of returned items per page; set to 0 to get available data altogether (used for pagination) |
| `offset` |  |  | The beginning index of the item being returned in the list (used for pagination) |
| `order_by` |  |  | The name of the field to sort on; must be an integer, float, boolean, string, or date field |
| `order` |  |  | The sort order for the result set, specified in conjunction with the order_by parameter |


**GET - ServerAttributeType**

Create server attribute type

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `Payload` |  | ✓ | POST method's JSON data |


### /server_attribute_type/{server_attribute_type_id}

**GET - ServerAttributeType**

Get server attribute type

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `server_attribute_type_id` |  | ✓ | Server attribute type id |
| `full` |  |  | If set to true, resolves all urls to actual objects |


**GET - ServerAttributeType**

Update server attribute type

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `server_attribute_type_id` |  | ✓ | Server attribute type id |
| `Payload` |  | ✓ | PUT method's JSON data |


**GET - ServerAttributeType**

Delete server attribute type

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `server_attribute_type_id` |  | ✓ | Server attribute type id |


---

<a name="server-group"></a>
## server_group

### /server_group

**GET - ServerGroup**

Get server groups

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `full` |  |  | If set to true, resolves all urls to actual objects |
| `limit` |  |  | The number of returned items per page; set to 0 to get available data altogether (used for pagination) |
| `offset` |  |  | The beginning index of the item being returned in the list (used for pagination) |
| `order_by` |  |  | The name of the field to sort on; must be an integer, float, boolean, string, or date field |
| `order` |  |  | The sort order for the result set, specified in conjunction with the order_by parameter |
| `name` |  |  | Filter results by name |
| `tags` |  |  | Filter results by tags (comma separated) |
| `root_only` |  |  |  |


**GET - ServerGroup**

Create server group

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `root_only` |  |  |  |
| `Payload` |  | ✓ | POST method's JSON data |


### /server_group/{server_group_id}

**GET - ServerGroup**

Get server group

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `server_group_id` |  | ✓ | Server group id |
| `full` |  |  | If set to true, resolves all urls to actual objects |
| `root_only` |  |  |  |


**GET - ServerGroup**

Update server group

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `server_group_id` |  | ✓ | Server group id |
| `root_only` |  |  |  |
| `Payload` |  | ✓ | PUT method's JSON data |


**GET - ServerGroup**

Delete server group

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `server_group_id` |  | ✓ | Server group id |
| `root_only` |  |  |  |


### /server_group/{server_group_id}/apply_monitoring_policy

**GET - ApplyMonitoringPolicy**

Apply monitoring policy

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `server_group_id` |  | ✓ | Server group id |


### /server_group/{server_group_id}/compound_service

**GET - CompoundService**

Get server group's compound services

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `server_group_id` |  | ✓ | Server group id |
| `full` |  |  | If set to true, resolves all urls to actual objects |
| `limit` |  |  | The number of returned items per page; set to 0 to get available data altogether (used for pagination) |
| `offset` |  |  | The beginning index of the item being returned in the list (used for pagination) |
| `order_by` |  |  | The name of the field to sort on; must be an integer, float, boolean, string, or date field |
| `order` |  |  | The sort order for the result set, specified in conjunction with the order_by parameter |
| `name` |  |  | Filter results by name |
| `tags` |  |  | Filter results by tags (comma separated) |


### /server_group/{server_group_id}/onsight

**GET - Onsight**

Get server group's onsights

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `server_group_id` |  | ✓ | Server group id |
| `full` |  |  | If set to true, resolves all urls to actual objects |
| `limit` |  |  | The number of returned items per page; set to 0 to get available data altogether (used for pagination) |
| `offset` |  |  | The beginning index of the item being returned in the list (used for pagination) |
| `order_by` |  |  | The name of the field to sort on; must be an integer, float, boolean, string, or date field |
| `order` |  |  | The sort order for the result set, specified in conjunction with the order_by parameter |
| `name` |  |  | Filter results by name |


### /server_group/{server_group_id}/server

**GET - Server**

Get server group's servers

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `server_group_id` |  | ✓ | Server group id |
| `full` |  |  | If set to true, resolves all urls to actual objects |
| `limit` |  |  | The number of returned items per page; set to 0 to get available data altogether (used for pagination) |
| `offset` |  |  | The beginning index of the item being returned in the list (used for pagination) |
| `order_by` |  |  | The name of the field to sort on; must be an integer, float, boolean, string, or date field |
| `order` |  |  | The sort order for the result set, specified in conjunction with the order_by parameter |
| `name` |  |  | Filter results by name |
| `fqdn` |  |  | Filter results by fqdn |
| `server_key` |  |  | Filter results by server_key |
| `partner_server_id` |  |  | Filter results by partner_server_id |
| `tags` |  |  | Filter results by tags (comma separated) |
| `attributes` |  |  | Filter results by attribute {name:value} pairs (comma separated) |
| `server_group` |  |  | Filter results by server_group id |
| `status` |  |  | Filter results by status |


### /server_group/{server_group_id}/server_group

**GET - ServerGroup**

Get server group's server groups

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `server_group_id` |  | ✓ | Server group id |
| `full` |  |  | If set to true, resolves all urls to actual objects |
| `limit` |  |  | The number of returned items per page; set to 0 to get available data altogether (used for pagination) |
| `offset` |  |  | The beginning index of the item being returned in the list (used for pagination) |
| `order_by` |  |  | The name of the field to sort on; must be an integer, float, boolean, string, or date field |
| `order` |  |  | The sort order for the result set, specified in conjunction with the order_by parameter |
| `name` |  |  | Filter results by name |
| `tags` |  |  | Filter results by tags (comma separated) |
| `root_only` |  |  |  |


### /server_group/{server_group_id}/templates

**GET - Templates**

Get server group's templatess

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `server_group_id` |  | ✓ | Server group id |
| `full` |  |  | If set to true, resolves all urls to actual objects |
| `limit` |  |  | The number of returned items per page; set to 0 to get available data altogether (used for pagination) |
| `offset` |  |  | The beginning index of the item being returned in the list (used for pagination) |
| `order_by` |  |  | The name of the field to sort on; must be an integer, float, boolean, string, or date field |
| `order` |  |  | The sort order for the result set, specified in conjunction with the order_by parameter |


**GET - Templates**

Create server group's templates

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `server_group_id` |  | ✓ | Server group id |
| `Payload` |  | ✓ | POST method's JSON data |


### /server_group/{server_group_id}/templates/{templates_id}

**GET - Templates**

Delete server group's templates

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `server_group_id` |  | ✓ | Server group id |
| `templates_id` |  | ✓ | Templates id |


---

<a name="server-template"></a>
## server_template

### /server_template

**GET - ServerTemplate**

Get server templates

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `full` |  |  | If set to true, resolves all urls to actual objects |
| `limit` |  |  | The number of returned items per page; set to 0 to get available data altogether (used for pagination) |
| `offset` |  |  | The beginning index of the item being returned in the list (used for pagination) |
| `order_by` |  |  | The name of the field to sort on; must be an integer, float, boolean, string, or date field |
| `order` |  |  | The sort order for the result set, specified in conjunction with the order_by parameter |
| `tag_filter_mode` |  |  | Mode in which to filter tags, choices: [or, and] |
| `attribute_filter_mode` |  |  | Mode in which to filter attributes, choices: [or, and] |
| `name` |  |  | Filter results by name |
| `tags` |  |  | Filter results by tags (comma separated) |
| `attributes` |  |  | Filter results by attribute {name:value} pairs (comma separated) |
| `server_group` |  |  | Filter results by server_group id |


**GET - ServerTemplate**

Create server template

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `Payload` |  | ✓ | POST method's JSON data |


### /server_template/{server_template_id}

**GET - ServerTemplate**

Get server template

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `server_template_id` |  | ✓ | Server template id |
| `full` |  |  | If set to true, resolves all urls to actual objects |


**GET - ServerTemplate**

Update server template

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `server_template_id` |  | ✓ | Server template id |
| `Payload` |  | ✓ | PUT method's JSON data |


### /server_template/{server_template_id}/reapply

**GET - ReapplyTemplate**

Reapply the template

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `server_template_id` |  | ✓ | Server template id |
| `full` |  |  | If set to true, resolves all urls to actual objects |
| `` |  |  |  |


---

<a name="snmp-credential"></a>
## snmp_credential

### /snmp_credential

**GET - SnmpCredential**

Get snmp credentials

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `full` |  |  | If set to true, resolves all urls to actual objects |
| `limit` |  |  | The number of returned items per page; set to 0 to get available data altogether (used for pagination) |
| `offset` |  |  | The beginning index of the item being returned in the list (used for pagination) |
| `order_by` |  |  | The name of the field to sort on; must be an integer, float, boolean, string, or date field |
| `order` |  |  | The sort order for the result set, specified in conjunction with the order_by parameter |


**GET - SnmpCredential**

Create snmp credential

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `Payload` |  | ✓ | POST method's JSON data |


### /snmp_credential/{snmp_credential_id}

**GET - SnmpCredential**

Get snmp credential

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `snmp_credential_id` |  | ✓ | Snmp credential id |
| `full` |  |  | If set to true, resolves all urls to actual objects |


**GET - SnmpCredential**

Update snmp credential

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `snmp_credential_id` |  | ✓ | Snmp credential id |
| `Payload` |  | ✓ | PUT method's JSON data |


**GET - SnmpCredential**

Delete snmp credential

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `snmp_credential_id` |  | ✓ | Snmp credential id |


---

<a name="status-page"></a>
## status_page

### /status_page

**GET - StatusPage**

Create status page

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `Payload` |  | ✓ | POST method's JSON data |


### /status_page/{status_page_id}

**GET - StatusPage**

Update status page

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `status_page_id` |  | ✓ | Status page id |
| `Payload` |  | ✓ | PUT method's JSON data |


**GET - StatusPage**

Delete status page

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `status_page_id` |  | ✓ | Status page id |


---

<a name="timezone"></a>
## timezone

### /timezone

**GET - Timezone**

Get timezones

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `full` |  |  | If set to true, resolves all urls to actual objects |
| `limit` |  |  | The number of returned items per page; set to 0 to get available data altogether (used for pagination) |
| `offset` |  |  | The beginning index of the item being returned in the list (used for pagination) |
| `order_by` |  |  | The name of the field to sort on; must be an integer, float, boolean, string, or date field |
| `order` |  |  | The sort order for the result set, specified in conjunction with the order_by parameter |


### /timezone/{timezone_id}

**GET - Timezone**

Get timezone

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `timezone_id` |  | ✓ | Timezone id |
| `full` |  |  | If set to true, resolves all urls to actual objects |


---

<a name="user"></a>
## user

### /user

**GET - User**

Get users

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `full` |  |  | If set to true, resolves all urls to actual objects |
| `limit` |  |  | The number of returned items per page; set to 0 to get available data altogether (used for pagination) |
| `offset` |  |  | The beginning index of the item being returned in the list (used for pagination) |
| `order_by` |  |  | The name of the field to sort on; must be an integer, float, boolean, string, or date field |
| `order` |  |  | The sort order for the result set, specified in conjunction with the order_by parameter |
| `username` |  |  | Filter results by username |


**GET - User**

Create user

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `Payload` |  | ✓ | POST method's JSON data |


### /user/getaddons

**GET - Get_addons**

Get addons

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `full` |  |  | If set to true, resolves all urls to actual objects |
| `user_id` |  | ✓ | Id of the user |


### /user/{user_id}

**GET - User**

Get user

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `user_id` |  | ✓ | User id |
| `full` |  |  | If set to true, resolves all urls to actual objects |


**GET - User**

Update user

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `user_id` |  | ✓ | User id |
| `Payload` |  | ✓ | PUT method's JSON data |


**GET - User**

Delete user

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `user_id` |  | ✓ | User id |


---

