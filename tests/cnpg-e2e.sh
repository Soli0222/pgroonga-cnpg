#!/usr/bin/env bash
set -euo pipefail

image=${1:?Usage: bash tests/cnpg-e2e.sh IMAGE PGROONGA_VERSION PG_MAJOR}
expected_version=${2:?Expected PGroonga version required}
pg_major=${3:?Expected PostgreSQL major required}
kind_cluster="pgroonga-e2e-${RANDOM}"
script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
# shellcheck source=.github/e2e.env
source "$script_dir/../.github/e2e.env"
export KUBECONFIG
KUBECONFIG=$(mktemp)

cleanup() {
  result=$?
  if [ "$result" -ne 0 ] && [ -s "$KUBECONFIG" ]; then
    kubectl get pods -A -o wide || true
    kubectl describe cluster pgroonga-e2e || true
    kubectl get events -A --sort-by=.lastTimestamp || true
    kubectl logs -n cnpg-system deployment/cnpg-controller-manager --tail=100 || true
    kubectl logs -l cnpg.io/cluster=pgroonga-e2e --all-containers --tail=100 || true
  fi
  kind delete cluster --name "$kind_cluster" || true
  rm -f "$KUBECONFIG"
  exit "$result"
}
trap cleanup EXIT

test "$(kind version | awk '{print $2}')" = "v${KIND_VERSION}" || {
  echo "Install kind v${KIND_VERSION} to match .github/e2e.env" >&2
  exit 1
}
kind create cluster --name "$kind_cluster" --image "$KIND_NODE_IMAGE" --wait 180s
kind load docker-image "$image" --name "$kind_cluster"
kubectl apply --server-side -f "https://raw.githubusercontent.com/cloudnative-pg/cloudnative-pg/v${CNPG_VERSION}/releases/cnpg-${CNPG_VERSION}.yaml"
kubectl rollout status -n cnpg-system deployment/cnpg-controller-manager --timeout=180s
kubectl apply -f - <<YAML
apiVersion: postgresql.cnpg.io/v1
kind: Cluster
metadata:
  name: pgroonga-e2e
spec:
  imageName: ${image}
  imagePullPolicy: Never
  instances: 1
  storage:
    size: 1Gi
YAML
kubectl wait --for=condition=Ready cluster/pgroonga-e2e --timeout=300s
pod=$(kubectl get cluster pgroonga-e2e -o jsonpath='{.status.currentPrimary}')
test "$(kubectl exec "$pod" -c postgres -- id -u)" = 26
test "$(kubectl exec "$pod" -c postgres -- id -g)" = 26

kubectl exec -i "$pod" -c postgres -- psql -U postgres -d app -v ON_ERROR_STOP=1 <<'SQL'
CREATE EXTENSION pgroonga;
CREATE TABLE documents (body text);
INSERT INTO documents VALUES ('日本語の全文検索を確認'), ('対象外');
CREATE INDEX documents_body_idx ON documents USING pgroonga (body);
SET enable_seqscan = off;
DO $$
BEGIN
  IF (SELECT count(*) FROM documents WHERE body &@ '全文検索') <> 1 THEN
    RAISE EXCEPTION 'Japanese full-text search failed';
  END IF;
END $$;
SQL
actual_version=$(kubectl exec "$pod" -c postgres -- psql -U postgres -d app -Atc "SELECT extversion FROM pg_extension WHERE extname = 'pgroonga'")
test "$actual_version" = "$expected_version"
actual_pg=$(kubectl exec "$pod" -c postgres -- psql -U postgres -d app -Atc "SELECT current_setting('server_version_num')::int / 10000")
test "$actual_pg" = "$pg_major"
echo "CNPG E2E passed: $image (UID/GID 26, PostgreSQL $actual_pg, PGroonga $actual_version)"
