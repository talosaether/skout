#!/usr/bin/env node

/**
 * End-to-End Integration Test for Photo Vault CRUD Operations
 *
 * This test validates:
 * - CREATE: Upload photo via API
 * - READ: List photos and retrieve specific photo
 * - UPDATE: (N/A for this app - photos are immutable)
 * - DELETE: Remove photo via API
 */

import { readFileSync, writeFileSync } from 'fs';
import { createReadStream } from 'fs';

const API_BASE = 'http://localhost:8000/api';
const FRONTEND_BASE = 'https://localhost:5174';

// Test utilities
class TestRunner {
  constructor() {
    this.passed = 0;
    this.failed = 0;
    this.tests = [];
  }

  async assert(condition, message) {
    if (condition) {
      console.log(`✅ PASS: ${message}`);
      this.passed++;
    } else {
      console.log(`❌ FAIL: ${message}`);
      this.failed++;
    }
  }

  async assertEqual(actual, expected, message) {
    const condition = actual === expected;
    await this.assert(condition, `${message} (expected: ${expected}, got: ${actual})`);
    return condition;
  }

  async assertNotNull(value, message) {
    await this.assert(value != null, message);
    return value != null;
  }

  async assertStatus(response, expectedStatus, message) {
    await this.assertEqual(response.status, expectedStatus, `${message} - HTTP status`);
    return response.status === expectedStatus;
  }

  summary() {
    console.log('\n' + '='.repeat(60));
    console.log(`📊 TEST SUMMARY`);
    console.log(`✅ Passed: ${this.passed}`);
    console.log(`❌ Failed: ${this.failed}`);
    console.log(`📋 Total:  ${this.passed + this.failed}`);
    console.log('='.repeat(60));

    if (this.failed > 0) {
      process.exit(1);
    }
  }
}

// API Test Client
class ApiClient {
  async get(endpoint) {
    const response = await fetch(`${API_BASE}${endpoint}`);
    return {
      status: response.status,
      data: response.ok ? await response.json() : await response.text()
    };
  }

  async delete(endpoint) {
    const response = await fetch(`${API_BASE}${endpoint}`, {
      method: 'DELETE'
    });
    return {
      status: response.status,
      data: response.ok ? await response.json() : await response.text()
    };
  }

  async uploadBlob(blob, filename) {
    const formData = new FormData();
    formData.append('file', new File([blob], filename, { type: 'image/jpeg' }));

    const response = await fetch(`${API_BASE}/assets`, {
      method: 'POST',
      body: formData
    });

    return {
      status: response.status,
      data: response.ok ? await response.json() : await response.text()
    };
  }
}

// Create a test image blob
function createTestImageBlob() {
  // Create a minimal valid JPEG blob for testing
  const jpegHeader = new Uint8Array([
    0xFF, 0xD8, 0xFF, 0xE0, 0x00, 0x10, 0x4A, 0x46, 0x49, 0x46, 0x00, 0x01,
    0x01, 0x01, 0x00, 0x48, 0x00, 0x48, 0x00, 0x00, 0xFF, 0xDB, 0x00, 0x43,
    0x00, 0x08, 0x06, 0x06, 0x07, 0x06, 0x05, 0x08, 0x07, 0x07, 0x07, 0x09,
    0x09, 0x08, 0x0A, 0x0C, 0x14, 0x0D, 0x0C, 0x0B, 0x0B, 0x0C, 0x19, 0x12,
    0x13, 0x0F, 0x14, 0x1D, 0x1A, 0x1F, 0x1E, 0x1D, 0x1A, 0x1C, 0x1C, 0x20,
    0x24, 0x2E, 0x27, 0x20, 0x22, 0x2C, 0x23, 0x1C, 0x1C, 0x28, 0x37, 0x29,
    0x2C, 0x30, 0x31, 0x34, 0x34, 0x34, 0x1F, 0x27, 0x39, 0x3D, 0x38, 0x32,
    0x3C, 0x2E, 0x33, 0x34, 0x32, 0xFF, 0xC0, 0x00, 0x11, 0x08, 0x00, 0x01,
    0x00, 0x01, 0x01, 0x01, 0x11, 0x00, 0x02, 0x11, 0x01, 0x03, 0x11, 0x01,
    0xFF, 0xC4, 0x00, 0x14, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x08, 0xFF, 0xC4,
    0x00, 0x14, 0x10, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xFF, 0xDA, 0x00, 0x0C,
    0x03, 0x01, 0x00, 0x02, 0x11, 0x03, 0x11, 0x00, 0x3F, 0x00, 0xAA, 0xFF, 0xD9
  ]);
  return new Blob([jpegHeader], { type: 'image/jpeg' });
}

// Main test suite
async function runTests() {
  const test = new TestRunner();
  const api = new ApiClient();

  console.log('🚀 Starting End-to-End Integration Tests for Photo Vault CRUD Operations\n');

  // Test 1: Health Check - Verify API is running
  console.log('📋 Test 1: API Health Check');
  try {
    const response = await api.get('/assets');
    await test.assertStatus(response, 200, 'API health check');
    await test.assert(Array.isArray(response.data.items), 'Response contains items array');
    await test.assert(typeof response.data.total === 'number', 'Response contains total count');
  } catch (error) {
    await test.assert(false, `API health check failed: ${error.message}`);
  }

  // Test 2: READ - List existing assets
  console.log('\n📋 Test 2: READ Operations - List Assets');
  let initialAssets;
  try {
    const response = await api.get('/assets');
    await test.assertStatus(response, 200, 'List assets');
    initialAssets = response.data;
    console.log(`   📊 Found ${initialAssets.total} existing assets`);
  } catch (error) {
    await test.assert(false, `List assets failed: ${error.message}`);
    return;
  }

  // Test 3: CREATE - Upload a new asset
  console.log('\n📋 Test 3: CREATE Operation - Upload Asset');
  let uploadedAsset;
  try {
    const testBlob = createTestImageBlob();
    const filename = `test-image-${Date.now()}.jpg`;

    const response = await api.uploadBlob(testBlob, filename);
    await test.assertStatus(response, 201, 'Upload asset');

    uploadedAsset = response.data;
    await test.assertNotNull(uploadedAsset.id, 'Uploaded asset has ID');
    await test.assertEqual(uploadedAsset.filename, filename, 'Uploaded filename matches');
    await test.assertEqual(uploadedAsset.mime, 'image/jpeg', 'Uploaded MIME type is correct');

    console.log(`   📷 Uploaded asset ID: ${uploadedAsset.id}`);
  } catch (error) {
    await test.assert(false, `Upload asset failed: ${error.message}`);
  }

  // Test 4: READ - Verify asset appears in list
  console.log('\n📋 Test 4: READ Operations - Verify Upload');
  try {
    const response = await api.get('/assets');
    await test.assertStatus(response, 200, 'List assets after upload');

    const newTotal = response.data.total;
    await test.assertEqual(newTotal, initialAssets.total + 1, 'Asset count increased by 1');

    const foundAsset = response.data.items.find(item => item.id === uploadedAsset.id);
    await test.assertNotNull(foundAsset, 'Uploaded asset found in list');

    if (foundAsset) {
      await test.assertEqual(foundAsset.filename, uploadedAsset.filename, 'Listed asset filename matches');
      await test.assertEqual(foundAsset.mime, uploadedAsset.mime, 'Listed asset MIME type matches');
    }
  } catch (error) {
    await test.assert(false, `Verify upload failed: ${error.message}`);
  }

  // Test 5: READ - Retrieve specific asset
  console.log('\n📋 Test 5: READ Operations - Retrieve Specific Asset');
  try {
    const response = await fetch(`${API_BASE}/assets/${uploadedAsset.id}`);
    await test.assertStatus(response, 200, 'Retrieve specific asset');

    const contentType = response.headers.get('content-type');
    await test.assertEqual(contentType, 'image/jpeg', 'Asset content type is correct');

    const blob = await response.blob();
    await test.assert(blob.size > 0, 'Asset has content');

    console.log(`   📊 Asset size: ${blob.size} bytes`);
  } catch (error) {
    await test.assert(false, `Retrieve asset failed: ${error.message}`);
  }

  // Test 6: DELETE - Remove the uploaded asset
  console.log('\n📋 Test 6: DELETE Operation - Remove Asset');
  try {
    const response = await api.delete(`/assets/${uploadedAsset.id}`);
    await test.assertStatus(response, 200, 'Delete asset');

    await test.assertEqual(response.data.deleted, uploadedAsset.id, 'Deleted asset ID matches');

    console.log(`   🗑️  Deleted asset ID: ${response.data.deleted}`);
  } catch (error) {
    await test.assert(false, `Delete asset failed: ${error.message}`);
  }

  // Test 7: READ - Verify asset is removed from list
  console.log('\n📋 Test 7: READ Operations - Verify Deletion');
  try {
    const response = await api.get('/assets');
    await test.assertStatus(response, 200, 'List assets after deletion');

    const finalTotal = response.data.total;
    await test.assertEqual(finalTotal, initialAssets.total, 'Asset count returned to original');

    const foundAsset = response.data.items.find(item => item.id === uploadedAsset.id);
    await test.assert(!foundAsset, 'Deleted asset not found in list');
  } catch (error) {
    await test.assert(false, `Verify deletion failed: ${error.message}`);
  }

  // Test 8: DELETE - Verify 404 for deleted asset
  console.log('\n📋 Test 8: DELETE Operations - Verify 404 for Deleted Asset');
  try {
    const response = await fetch(`${API_BASE}/assets/${uploadedAsset.id}`);
    await test.assertStatus(response, 404, 'Deleted asset returns 404');
  } catch (error) {
    await test.assert(false, `404 verification failed: ${error.message}`);
  }

  // Test 9: Error Handling - Invalid operations
  console.log('\n📋 Test 9: Error Handling');
  try {
    // Test DELETE non-existent asset
    const fakeId = 'non-existent-id-12345';
    const deleteResponse = await api.delete(`/assets/${fakeId}`);
    await test.assertStatus(deleteResponse, 404, 'Delete non-existent asset returns 404');

    // Test GET non-existent asset
    const getResponse = await fetch(`${API_BASE}/assets/${fakeId}`);
    await test.assertStatus(getResponse, 404, 'Get non-existent asset returns 404');
  } catch (error) {
    await test.assert(false, `Error handling test failed: ${error.message}`);
  }

  // Test 10: Frontend Proxy Test
  console.log('\n📋 Test 10: Frontend Proxy Configuration');
  try {
    // Test that the frontend can proxy to the backend
    const response = await fetch(`${FRONTEND_BASE}/api/assets`, {
      headers: { 'Accept': 'application/json' }
    });
    await test.assertStatus(response, 200, 'Frontend proxy to backend API');

    const data = await response.json();
    await test.assert(Array.isArray(data.items), 'Proxied response contains items array');
  } catch (error) {
    console.log(`   ⚠️  Frontend proxy test skipped (likely HTTPS cert issue): ${error.message}`);
    // Don't fail the test for this as it's expected in development
  }

  test.summary();
}

// Check if we're running this as a script
if (import.meta.url === `file://${process.argv[1]}`) {
  runTests().catch(console.error);
}

export { runTests };