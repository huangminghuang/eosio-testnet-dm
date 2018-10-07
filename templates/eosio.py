"""Create configuration to deploy Kubernetes resources."""

# from templates.helpers import logging, boot_nodeos, nodeos_wrapper
import json

def configMap(context, name_prefix, type_prefix):
  genesis = context.properties['genesis'].copy()
  genesis['initial_key'] = genesis['signatureProvider'].split('=KEY:')[0]
  genesis.pop('signatureProvider', None)
    
  name=name_prefix+"-configmap"
  return {
    'name': name ,
    'type': type_prefix + 'configmaps',
    'metadata': {
      'dependsOn': [
        context.properties['clusterType']
      ]
    },
    'properties': {
      'apiVersion': 'v1',
      'kind': 'ConfigMap',
      'namespace': 'default',
      'metadata': {
        'name': name,
        'labels': {
            'id': 'deployment-manager'
        }
      },
      'data': {
        'genesis.json': json.dumps(genesis),
        'logging.json': json.dumps(context.properties['logging']),
        'boot-nodeos.sh': context.properties['boot-nodeos.sh'],
        'nodeos_wrapper.sh': context.properties['nodeos_wrapper.sh']
      }
    }
  }
    

def biosDeployment(context, name_prefix, type_prefix):
  name=name_prefix+"-bios"
  return {
    'name': name,
    'type': type_prefix + 'deployments',
    'metadata': {
      'dependsOn': [
        context.properties['clusterTypeApps']
      ]
    },
    'properties': {
      'apiVersion': 'apps/v1',
      'kind': 'Deployment',
      'namespace': 'default',
      'metadata': {
        'name': name
      },
      'spec': {
        'replicas': 1,
        'selector': {
          'matchLabels': {
            'name': name,
            'app': 'bios'
          }
        },
        'template': {
          'metadata': {
            'labels': {
              'name': name,
              'app': 'bios'
            }
          },
          'spec': {
            'containers': [{
              'name': 'container',
              'image': context.properties['image'],
              'command': ['bash', '/eosio/nodeos_wrapper.sh', 
                          '--plugin', 'eosio::chain_api_plugin', '--plugin', 'eosio::history_api_plugin',
                          '--plugin', 'eosio::http_plugin', '--http-server-address', '0.0.0.0:8888', '--http-validate-host', 'false', '--p2p-listen-endpoint', '0.0.0.0:9876', 
                          '--enable-stale-production', '--producer-name', 'eosio',
                          '--genesis-json', '/eosio/genesis.json',
                          '--signature-provider', context.properties['genesis']['signatureProvider'],
                          '--logconf', '/eosio/logging.json'],
              'args': context.properties['args'],
              'ports': [{
                'containerPort': 8888,
                'protocol': 'TCP'
              },{
                'containerPort': 9876,
                'protocol': 'TCP'
              }],  
              'readinessProbe': {
                'httpGet': {
                  'path': '/v1/chain/get_info',
                  'port': 8888 
                 }
              },
              'volumeMounts': [{
                'name': 'config-volume',
                'mountPath': "/eosio"
              }]
            }],
            'volumes':[{
              'name': 'config-volume',
              'configMap': {
                'name': name_prefix + '-configmap'
              }
            }]
          }
        }
      }
    }
  }
  
def biosService(context, name_prefix, type_prefix):
  name=name_prefix+"-bios-svc"
  return {
    'name': name,
    'type': type_prefix + 'services',
    'metadata': {
      'dependsOn': [
        context.properties['clusterType']
      ]
    },
    'properties': {
      'apiVersion': 'v1',
      'kind': 'Service',
      'namespace': 'default',
      'metadata': {
        'name': name,
        'labels': {
          'id': 'deployment-manager'
        }
      },
      'spec': {
        'type': 'ClusterIP',
        'ports': [{
          'port': 8888,
          'targetPort': 8888,
          'protocol': 'TCP',
          'name': 'http'
        },{
          'port': 9876,
          'targetPort': 9876,
          'protocol': 'TCP',
          'name': 'peer-to-peer'
        }],
        'selector': {
          'app': 'bios',
          'name': name_prefix + "-bios"
        }
      }
    }
  }
  
def nodeosService(context, name_prefix, type_prefix):
  service = context.properties.get('service', {'port': 8888, 'type': 'LoadBalancer'})
  name=name_prefix+"-nodeos-svc"
  return {
    'name': name,
    'type': type_prefix + 'services',
    'metadata': {
      'dependsOn': [
        context.properties['clusterType']
      ]
    },
    'properties': {
      'apiVersion': 'v1',
      'kind': 'Service',
      'namespace': 'default',
      'metadata': {
        'name': name,
        'labels': {
          'id': 'deployment-manager'
        }
      },
      'spec': {
        'type': service['type'],
        'ports': [{
          'port': service['port'],
          'targetPort': 8888,
          'protocol': 'TCP',
          'name': 'http'
        }],
        'selector': {
          'name': name_prefix + "-nodeos",
          "app": "nodeos"
        }
      }
    }
  }
  
def nodeosHeadlessService(context, name_prefix, type_prefix):
  name=name_prefix+"-headless"
  return {
    'name': name,
    'type': type_prefix + 'services',
    'metadata': {
      'dependsOn': [
        context.properties['clusterType']
      ]
    },
    'properties': {
      'apiVersion': 'v1',
      'kind': 'Service',
      'namespace': 'default',
      'metadata': {
        'name': name,
        'labels': {
          'id': 'deployment-manager'
        }
      },
      'spec': {
        'clusterIP': 'None',
        'ports': [{
          'port': 8888,
          'targetPort': 8888,
          'protocol': 'TCP',
          'name': 'http'
        },{
          'port': 9876,
          'targetPort': 9876,
          'protocol': 'TCP',
          'name': 'peer-to-peer'
        }],
        'selector': {
          'name': name_prefix + "-nodeos",
          "app": "nodeos"
        }
      }
    }
  }
    
def statefulSet(context, name_prefix, type_prefix):
  name=name_prefix+"-nodeos"
  result = {
    'name': name,
    'type': type_prefix + 'statefulsets',
    'metadata': {
      'dependsOn': [
        context.properties['clusterTypeApps']
      ]
    },
    'properties': {
      'apiVersion': 'apps/v1',
      'kind': 'StatefulSet',
      'namespace': 'default',
      'metadata': {
        'name': name
      },
      'spec': {
        'replicas': context.properties['replicas'],
        'selector': {
          "matchLabels": {
            'name': name,
            "app": "nodeos"
          }
        },
        "serviceName": name + "-headless",
        'template': {
          'metadata': {
            'labels': {
              'name': name,
              'app': 'nodeos'
            }
          },
          'spec': {
            'containers': [{
              'name': name,
              'image': context.properties['image'],
              'command': ['bash', '/eosio/boot-nodeos.sh'],
              'args': context.properties['args'],
              'env': [{
                'name': 'BIOS_ADDR',
                'value': name_prefix + '-bios-svc:8888'
              },{
                'name': 'NODEOS',
                'value': str(context.properties['replicas'])
              },{
                'name': 'PRODUCERS',
                'value': str(context.properties['producers'])
              },{
                'name': 'GENESISKEY',
                'value': context.properties['genesis']['signatureProvider']
              },{
                'name': 'SERVICE_PATTERN',
                'value': name + "-{}." + name_prefix + "-headless"
              }],
              'ports': [{
                'containerPort': 8888,
                'protocol': 'TCP'
              },{
                'containerPort': 9876,
                'protocol': 'TCP'
              }],  
              'readinessProbe': {
                'httpGet': {
                  'path': '/v1/chain/get_info',
                  'port': 8888 
                 }
              },
              'volumeMounts': [{
                'name': 'config-volume',
                'mountPath': "/eosio"
              }]
            }],
            'volumes':[{
              'name': 'config-volume',
              'configMap': {
                'name': name_prefix + '-configmap'
              }
            }]
          }
        }
      }
    }
  }
  persistence = context.properties.get('persistence', { 'enabled': False, 'size': '100Gi'})
  if persistence['enabled']:
    result['properties']['spec']['template']['spec']['containers'][0]['volumeMounts'].append({'name': 'data', 'mountPath': '/root/.local/share/eosio'})
    result['properties']['spec']['volumeTemplates'] = [{
      'metadata': {
        'name': 'data',
        'labels': {
          'name': name,
          'app': 'nodeos'
        }
      },
      'spec': {
        'accessModes': [ "ReadWriteOnce" ],
        'resources': {
          'requests': {
            'storage': persistence['size']
          }
        }
      }
    }]
  return result

def GenerateConfig(context):
  """Generate YAML resource configuration."""
    
  cluster_type_prefix = '{}/{}:/api/v1/namespaces/{{namespace}}/'.format(context.env['project'],context.properties['clusterType'])  
  cluster_type_apps_prefix = '{}/{}:/apis/apps/v1/namespaces/{{namespace}}/'.format(context.env['project'],context.properties['clusterTypeApps'])
  
  name_prefix = context.env['deployment'] + '-' + context.env['name']
  resources = [
    configMap(context, name_prefix, cluster_type_prefix),
    biosDeployment(context, name_prefix, cluster_type_apps_prefix),
    biosService(context, name_prefix, cluster_type_prefix),
    nodeosService(context, name_prefix, cluster_type_prefix),
    nodeosHeadlessService(context, name_prefix, cluster_type_prefix),
    statefulSet(context, name_prefix, cluster_type_apps_prefix)
  ]
  return {'resources': resources}
