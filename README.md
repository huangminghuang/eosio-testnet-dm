# eosio-testnet-dm: Deploy a EOSIO Testnet on Google Kubernetes Engine
This is a Google Deployment Manager template to create a GKE cluster and deployment a EOSIO Testnet on the cluster.  It exposes a single HTTP endpoint at port 8888 for cleos to connect to. 

Notice that this solution is only for GKE. If you need to deploy a EOSIO Testnet on an exising kubernets cluster, please use eosio-testnet[https://github.com/huangminghuang/eosio-testnet]. 
## Getting Started:

Modify eosio.yaml to adjust the parameters you need and then save it.
Next, start the cluster as follows.
```
$ NAME=eosio
$ gcloud deployment-manager deployments create ${NAME} --config=eosio.yaml
```


Before you can directly interfact with the cluster, you need to obtain the credential of the cluster
```
$ gcloud container clusters get-credentitials ${NAME}-cluster
```

The bootstraping process may take a few minutes to be ready. You can examine whether all the pods are ready
```bash
$ kubectl get pods
NAME                          READY     STATUS    RESTARTS   AGE
eosio-bios-644df44b65-g6dg8   1/1       Running   0          3m
eosio-nodeos-0                1/1       Running   0          3m
eosio-nodeos-1                1/1       Running   0          48s
eosio-nodeos-2                1/1       Running   0          30s
eosio-nodeos-3                1/1       Running   0          17s
```

To get the IP address for cleos to connect to
```bash
kubectl get svc --namespace default eosio-nodeos -o jsonpath='{.status.loadBalancer.ingress[0].ip}'
```



cleanup
```
gcloud deployment-manager deployments delete ${NAME}
```