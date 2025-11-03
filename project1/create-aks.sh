#!/bin/bash

# Variables
RESOURCE_GROUP="test-rg"
AKS_NAME="aksdemo18"

# Create AKS cluster
az aks create \
  --resource-group $RESOURCE_GROUP \
  --name $AKS_NAME \
  --node-count 2 \
  --generate-ssh-keys

# Get AKS credentials to access the cluster
az aks get-credentials --resource-group $RESOURCE_GROUP --name $AKS_NAME

# Verify
kubectl get nodes

kubectl config current-context
echo "AKS cluster '$AKS_NAME' created in resource group '$RESOURCE_GROUP'."