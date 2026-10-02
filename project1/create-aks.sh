#!/usr/bin/env bash
# Creates a small AKS cluster for the monitoring demo and loads its kubeconfig.
# Override the defaults with environment variables, for example:
#   RESOURCE_GROUP=my-rg AKS_NAME=my-aks LOCATION=westeurope ./create-aks.sh
set -euo pipefail

# Variables
RESOURCE_GROUP="${RESOURCE_GROUP:-test-rg}"
AKS_NAME="${AKS_NAME:-aksdemo18}"
LOCATION="${LOCATION:-centralindia}"
NODE_COUNT="${NODE_COUNT:-2}"

# Create the resource group (no-op if it already exists)
az group create --name "$RESOURCE_GROUP" --location "$LOCATION" --output none

# Create AKS cluster
az aks create \
  --resource-group "$RESOURCE_GROUP" \
  --name "$AKS_NAME" \
  --location "$LOCATION" \
  --node-count "$NODE_COUNT" \
  --generate-ssh-keys \
  --output none

# Get AKS credentials to access the cluster
az aks get-credentials --resource-group "$RESOURCE_GROUP" --name "$AKS_NAME" --overwrite-existing

# Verify
kubectl get nodes
kubectl config current-context
echo "AKS cluster '$AKS_NAME' created in resource group '$RESOURCE_GROUP'."
echo "Delete it when done: az group delete --name '$RESOURCE_GROUP' --yes --no-wait"
