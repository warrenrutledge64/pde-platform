#!/usr/bin/env bash
# Credential-free template: requires a separately configured READ-ONLY AWS CLI profile.
# DOES NOT create/change AWS resources. Do NOT commit output or paste raw output into chat.
set -euo pipefail
: "${AWS_PROFILE:?Set AWS_PROFILE to an authorized inventory-only profile; do not use production-seat credentials}"
REGION=us-east-1
OUT="${1:-}"
if [[ -z "$OUT" || "$OUT" != /* || -e "$OUT" ]]; then
  echo "Usage: AWS_PROFILE=<inventory-profile> bash $0 /absolute/new/private/output-dir" >&2
  exit 2
fi
umask 077
mkdir -m 700 -- "$OUT"
echo "Local PRIVATE inventory directory: $OUT"
aws --region "$REGION" sts get-caller-identity > "$OUT/caller-identity.json"
aws --region "$REGION" iam get-account-summary > "$OUT/iam-account-summary.json"
aws --region "$REGION" iam list-roles > "$OUT/iam-roles.json"
aws --region "$REGION" iam list-policies --scope Local > "$OUT/iam-local-policies.json"
aws --region "$REGION" iam list-users > "$OUT/iam-users.json"
aws --region "$REGION" iam list-groups > "$OUT/iam-groups.json"
aws --region "$REGION" iam list-open-id-connect-providers > "$OUT/iam-oidc-providers.json"
aws --region "$REGION" iam list-saml-providers > "$OUT/iam-saml-providers.json"
aws --region "$REGION" iam list-account-aliases > "$OUT/iam-account-aliases.json"
aws --region "$REGION" iam get-account-authorization-details > "$OUT/iam-authorization-details.json"
aws --region "$REGION" cloudtrail describe-trails --include-shadow-trails > "$OUT/cloudtrail-trails.json"
aws --region "$REGION" cloudtrail list-event-data-stores > "$OUT/cloudtrail-event-data-stores.json"
aws --region "$REGION" kms list-keys > "$OUT/kms-keys.json"
aws --region "$REGION" secretsmanager list-secrets > "$OUT/secrets-metadata.json"
aws --region "$REGION" lambda list-functions > "$OUT/lambda-functions.json"
aws --region "$REGION" dynamodb list-tables > "$OUT/dynamodb-tables.json"
echo "Inventory complete. Inspect/redact locally; do not commit or upload sensitive metadata."
echo "Additional per-resource policy review must be carried out separately by the Human security administrator."
