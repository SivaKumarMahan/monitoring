# monitoring
Create Monitoring Namespace
kubectl create namespace monitoring

Deploy Prometheus
kubectl apply -f prometheus-config.yaml
kubectl apply -f prometheus.yaml

Check Prometheus Deployment
kubectl get pods -n monitoring
kubectl get svc -n monitoring
kubectl get configmap -n monitoring

Deploy Grafana
kubectl apply -f grafana.yaml
kubectl get svc -n monitoring
External Ip: 20.219.204.44

Access Grafana UI
Added LoadBalancer to Grafana service. Use the external IP to access Grafana UI.
Open your browser and navigate to:
http://20.219.204.44
Username: admin
Password: admin123

Add Prometheus as Data Source in Grafana
In the Grafana UI:
Click ⚙️ (Gear icon) → Data Sources → Add data source
Choose Prometheus
Set URL: http://prometheus.monitoring.svc.cluster.local:9090
Click Save & Test
If successful, you can now create dashboards!

Deploy Node Exporter
kubectl apply -f nodeExporter.yaml
kubectl get daemonset -n monitoring
kubectl get pods -n monitoring
kubectl get svc -n monitoring

Deploying Node Exporter allows Prometheus and Grafana to visualize real-time node-level metrics such as CPU, memory, disk usage and network stats for each AKS worker node.

Access prometheus UI
Addedd LoadBalancer to Prometheus service. Use the external IP to access Prometheus UI.
Open your browser and navigate to:
http://13.71.63.193:9090

Import Pre-Built Dashboards in Grafana
In the Grafana UI:
Click ➕ (Plus icon) → Import
Enter Dashboard ID: 1860 (Node Exporter Full)
Click Load
Select Prometheus as the data source
Click Import

You’ll now see metrics for all AKS nodes (CPU, memory, disk, network, etc.).

Prometheus Instance Dashboard
For Prometheus itself (to monitor Prometheus performance):
In the Grafana UI:
Click ➕ (Plus icon) → Import
Enter Dashboard ID: 3662 (Prometheus Instance)
Click Load
Select Prometheus as the data source
Click Import

You can now monitor the health and performance of your Prometheus server.

Generate Pod-Level Load (for AKS Workloads)
If you want to see Kubernetes metrics, deploy a small test app and increase replicas.
kubectl create deployment load-demo --image=nginx
kubectl scale deployment load-demo --replicas=10

Access the load-demo application
You can port-forward to access the load-demo application locally:
kubectl port-forward deploy/load-demo 8080:80

Generate Traffic to See Metrics
To see real-time metrics in Grafana, generate some traffic on your AKS cluster. You can use a simple load testing tool like `hey` or `ab` to send requests to your application endpoints.
For example, using `hey`:
hey -z 5m -c 50 http://<your-application-endpoint>  

This will generate traffic for 5 minutes with a concurrency of 50 requests.
Replace `<your-application-endpoint>` with the actual endpoint of your application running in AKS.
This will help populate the dashboards with real-time data.

Send 1000 requests
ab -n 1000 -c 50 http://localhost:8080/
This will send a total of 1000 requests to the specified endpoint with a concurrency level of 50.   
Replace `http://localhost:8080/` with the actual endpoint of your application running in AKS.