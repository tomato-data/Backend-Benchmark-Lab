// scenarios/db-advanced/13-db-transactions.js
import http from "k6/http";
import { check, group } from "k6";
import { BASE_URL, defaultOptions } from "../config.js";

// 각 락 전략별로 다른 상품 사용 (격리된 환경)
const PRODUCTS = {
  noLock: 1,       // Product 1: No Lock 테스트용
  pessimistic: 2,  // Product 2: Pessimistic Lock 테스트용
  optimistic: 3,   // Product 3: Optimistic Lock 테스트용
  serializable: 4, // Product 4: Serializable 테스트용
};

export const options = {
  ...defaultOptions,
  thresholds: {
    "group_duration{group:::A. No Lock}": ["p(95)<500"],
    "group_duration{group:::B. Pessimistic Lock}": ["p(95)<1000"],
    "group_duration{group:::C. Optimistic Lock}": ["p(95)<1000"],
    "group_duration{group:::D. Serializable}": ["p(95)<1000"],
  },
};

export function setup() {
  // 테스트 전 모든 상품 재고 리셋
  http.post(`${BASE_URL}/transactions/reset`);
  console.log("All products reset to stock=1000, version=0");
}

export function teardown() {
  // 테스트 후 각 상품의 최종 재고 확인
  console.log("\n========== Final Stock Results ==========");

  for (const [strategy, productId] of Object.entries(PRODUCTS)) {
    const res = http.get(`${BASE_URL}/transactions/products/${productId}`);
    const data = res.json();
    console.log(`[${strategy}] Product ${productId}: stock=${data.stock}, version=${data.version}`);
  }

  console.log("==========================================\n");
}

export default function () {
  // ============================================
  // A. No Lock (Lost Update 발생 가능)
  // ============================================
  group("A. No Lock", function () {
    const res = http.post(
      `${BASE_URL}/transactions/decrement/no-lock?product_id=${PRODUCTS.noLock}&quantity=1`
    );
    check(res, {
      "no-lock status 200": (r) => r.status === 200,
      "no-lock success": (r) => r.json().success === true,
    });
  });

  // ============================================
  // B. Pessimistic Lock (FOR UPDATE)
  // ============================================
  group("B. Pessimistic Lock", function () {
    const res = http.post(
      `${BASE_URL}/transactions/decrement/pessimistic?product_id=${PRODUCTS.pessimistic}&quantity=1`
    );
    check(res, {
      "pessimistic status 200": (r) => r.status === 200,
      "pessimistic success": (r) => r.json().success === true,
    });
  });

  // ============================================
  // C. Optimistic Lock (Version 체크)
  // ============================================
  group("C. Optimistic Lock", function () {
    const res = http.post(
      `${BASE_URL}/transactions/decrement/optimistic?product_id=${PRODUCTS.optimistic}&quantity=1`
    );
    check(res, {
      "optimistic status 200": (r) => r.status === 200,
      "optimistic success": (r) => r.json().success === true,
    });
  });

  // ============================================
  // D. Serializable 격리 수준
  // ============================================
  group("D. Serializable", function () {
    const res = http.post(
      `${BASE_URL}/transactions/decrement/serializable?product_id=${PRODUCTS.serializable}&quantity=1`
    );
    check(res, {
      "serializable status 200": (r) => r.status === 200,
      "serializable success": (r) => r.json().success === true,
    });
  });
}
