import yaml

with open('docker-compose.yml', 'r') as f:
    config = yaml.safe_load(f)

# 1. RabbitMQ
if "15692:15692" not in config['services']['rabbitmq']['ports']:
    config['services']['rabbitmq']['ports'].append("15692:15692")
config['services']['rabbitmq']['command'] = 'sh -c "rabbitmq-plugins enable rabbitmq_prometheus; rabbitmq-server"'

# 2. Postgres Exporters
for i in range(1, 4):
    node_name = f'pg_nodo{i}'
    port = 9186 + i
    config['services'][f'postgres-exporter-nodo{i}'] = {
        'image': 'prometheuscommunity/postgres-exporter',
        'container_name': f'postgres_exporter_nodo{i}',
        'environment': {
            'DATA_SOURCE_NAME': f'postgresql://admin:admin@{node_name}:5432/historia_clinica?sslmode=disable'
        },
        'ports': [f'{port}:9187'],
        'depends_on': {
            node_name: {'condition': 'service_healthy'}
        },
        'restart': 'unless-stopped',
        'networks': ['historia_clinica_net']
    }

# 3. Prometheus
config['services']['prometheus'] = {
    'image': 'prom/prometheus',
    'container_name': 'prometheus',
    'ports': ['9090:9090'],
    'volumes': [
        './monitoring/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml'
    ],
    'restart': 'unless-stopped',
    'networks': ['historia_clinica_net']
}

# 4. Grafana
config['services']['grafana'] = {
    'image': 'grafana/grafana',
    'container_name': 'grafana',
    'ports': ['3000:3000'],
    'environment': {
        'GF_SECURITY_ADMIN_USER': 'admin',
        'GF_SECURITY_ADMIN_PASSWORD': 'admin'
    },
    'volumes': [
        'grafana_data:/var/lib/grafana',
        './monitoring/grafana/provisioning:/etc/grafana/provisioning',
        './monitoring/grafana/dashboards:/var/lib/grafana/dashboards'
    ],
    'restart': 'unless-stopped',
    'networks': ['historia_clinica_net']
}

# Add grafana volume
if 'volumes' not in config:
    config['volumes'] = {}
config['volumes']['grafana_data'] = None

with open('docker-compose.yml', 'w') as f:
    yaml.dump(config, f, sort_keys=False)

print("docker-compose.yml patched")
