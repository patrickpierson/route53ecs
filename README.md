**Route53ECS**

This is a route 53 service record generator for ecs. Copy the config.ini.sample to config.ini and fill in with your cluster name and route53 domain name.

Run with:
> python test.py

Recrods will be generated like this:
```
service.srv.domain.com. SRV 1 10 12345 172.16.1.11
```