=======
History
=======

1.0.0 (Unreleased)
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


0.1.0 (Unreleased)
------------------

* /__lbheartbeat__ endpoint to be used with load balancers. (ericof)
* Error views for 403, 404 and 50x status codes. (ericof)
* Initial implementation. (ericof)
