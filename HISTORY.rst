=======
History
=======

1.1.2 (Unreleased)
------------------
    * BODY-62: Implement Pagination on BaseResource (ericof).
    * BODY-64: Add like filter. (ericof)
    * BODY-88: Improve apply_secutiry to use context permissions (rudaporto).
    * BODY-89: Improve logging. (ericof).
    * BODY-90: Remove leading underscore from node names. (ericof).
    * Same as BODY-90 but also for relationship fields and fields of schema node attributes (rudaporto).
    * Implement security filters for all REST methods improving BaseResource.apply_security (rudaporto).
    * BaseFactory now append permission from model class using __acl__ class method (rudaporto).
    * Only try to apply security filter query if model is subclass of LocalRolesMixin (rudaporto).
    * Change BaseResource.default_filters hook to be a method: it receives and returns a query (with filters or params applied) (rudaporto).
    * Pin pyramid version to 1.7.3 (rudaporto).
    * Change create_filter_from_query_params to not use utils.data.native_value to convert string to integer (rudaporto).
    * Fix bug: apply security query was not applied in resource get_one (rudaporto).
    * New BaseResource class attribute: enable_security = True. This can be used in custom filters do disable apply_security (rudaporto).
    * Fix condition used to apply request on the model instance (rudaporto).


1.1.1 (2016-10-04)
------------------
    * BODY-54: Improve resource events to enable sqs message queue and workflow events. (rudaporto)
    * Move validate_id function to validator module and fix tests. (rudaporto)
    * BODY-58: Avoid transaction rollback when connection to internal user service fails. (rudaporto)
    * When id field is in the collection_post body, check if alredy exists a registry with same id. (rudaporto)

1.1.0 (2016-09-27)
------------------
    * Create groupfinder callback and add it Authentication policy (JWT). (rudaporto)
    * Create new class to represent the current Authenticated user object in request. (rudaporto)
    * Add user_factory function as request method user attribute: request.user. (rudaporto)
    * Refactory auth validation to isolate user_factory function. (rudaporto)
    * New base context factory class to be used in all resource class as factory parameter. (rudaporto)
    * Add RESTService base class for REST resources. (ericof)
    * Integrate pyramid_jwt as authentication policy with same secreta as briefy.rolleiflex. (rudaporto)
    * Add validate_jwt_token validator to all methods on base resource, only authenticated calls will be permited. (rudaporto)
    * New base class to create workflow REST service to get informantion and trigger transitions on models. (ericof)
    * New helper integrated into resource to user query filters on the collection_get method of resource. (ericof)
    * BODY-26: Avoid invalid ID raise ValueError when acl are being evaluated. (rudaporto)
    * Add serializer for AuthenticatedUser object. (rudaporto)
    * BODY-32: Attach current request in model instance after creation or loading in the resource. (rudaporto)
    * BODY-38: REST Resources: notify events for the model instance lifecycle (POST, PUT, GET, DELETE). (rudaporto)
    * BODY-39: Fix workflow resource POST transition. (rudaporto)
    * BODY-45: Fix workflow service POST transitions to return correct error codes. (rudaporto)
    * BODY-38: REST Resources: notify events for the model instance lifecycle (POST, PUT, GET, DELETE) (rudaporto)
    * BODY-39: Fix workflow resource POST transition (rudaporto)
    * BODY-44: Public information about a user. (ericof)
    * BODY-47: Add sqlalchemy listener events to inject request on model creation and load. (rudaporto)
    * New function to update state_history actor field with user map data. (rudaporto)
    * Fix workflow transition to not crash with empty message on body. (rudaporto)
    * BODY-62: Add pagination to resources. (ericof)


1.0.0 (2016-08-05)
------------------
    * /__lbheartbeat__ endpoint to be used with load balancers. (ericof)
    * Error views for 403, 404 and 50x status codes. (ericof)
    * Initial implementation. (ericof)

