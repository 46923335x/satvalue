# Printful + Bitcoin Checkout Roadmap

## Objective

Add merchandise sales to the existing website using Printful for print-on-demand fulfillment and Bitcoin as a customer payment option.

## Target Order Flow

1. Customer selects a product and variant.
2. Website calculates the order total in USD.
3. Checkout displays the live BTC equivalent.
4. Customer pays through a Bitcoin payment processor.
5. The site waits for payment confirmation.
6. Once confirmed, the order is submitted to Printful.
7. Printful charges the merchant’s saved fiat payment method.
8. Printful manufactures and ships the product.
9. Tracking information is synchronized back to the website and emailed to the customer.

## Implementation Tasks

### 1. Inspect the Existing Site

Identify:

* Framework and hosting environment
* Current ecommerce or cart functionality
* Database and authentication setup
* Existing payment integrations
* Deployment and environment-variable configuration

Do not replace the existing architecture unless necessary.

### 2. Add Printful Integration

Use Printful’s native integration when supported by the current platform. Otherwise, integrate through the Printful API.

Implement:

* Product and variant synchronization
* Product images and mockups
* Inventory availability
* Shipping-rate retrieval
* Order submission
* Order-status synchronization
* Shipment tracking updates

Store Printful product, variant, and order IDs in the local database.

### 3. Add Bitcoin Payments

Integrate a reputable Bitcoin payment gateway supported by the existing platform.

Requirements:

* Keep product prices denominated internally in USD
* Calculate the BTC amount at checkout using a live exchange rate
* Lock the quoted BTC price for a limited payment window
* Generate a unique invoice or payment address for each order
* Verify payment through signed webhooks
* Handle pending, confirmed, expired, underpaid, and overpaid payments
* Never trust payment status supplied by the browser

Prefer support for both on-chain Bitcoin and Lightning if available.

### 4. Create an Order State Machine

Use explicit order statuses:

* `cart`
* `awaiting_payment`
* `payment_pending`
* `paid`
* `submitted_to_printful`
* `in_production`
* `shipped`
* `completed`
* `payment_expired`
* `cancelled`
* `refunded`
* `fulfillment_error`

Only submit an order to Printful after the Bitcoin payment has reached the configured confirmation threshold.

Webhook processing must be idempotent so duplicate events cannot create duplicate Printful orders.

### 5. Add Checkout and Customer Messaging

Checkout should display:

* USD order total
* BTC amount
* Exchange-rate expiration time
* Network-fee notice
* Payment confirmation status
* Estimated production and shipping times
* Made-to-order disclosure
* Refund policy

Send emails for:

* Order received
* Bitcoin payment confirmed
* Order sent to production
* Order shipped
* Refund or fulfillment issue

### 6. Add Administration Controls

Provide an admin view showing:

* Customer order
* BTC invoice and transaction status
* USD value at the time of purchase
* Printful order status
* Fulfillment cost
* Gross margin
* Tracking number
* Errors requiring manual review

Include a manual retry option for failed Printful submissions.

### 7. Security and Reliability

Implement:

* Environment variables for all API credentials
* Webhook signature verification
* Server-side price validation
* Idempotency keys
* Structured error logging
* Rate limiting
* Retry logic with backoff
* Duplicate-order prevention
* No private keys stored in the application

### 8. Testing

Create automated and manual tests for:

* Successful BTC payment
* Expired invoice
* Delayed confirmation
* Underpayment
* Duplicate webhook
* Printful API failure
* Out-of-stock variant
* Invalid shipping address
* Refund
* Tracking synchronization

Use sandbox or test modes before enabling production payments.

### 9. Launch Sequence

1. Connect the Printful test store.
2. Add one hat and one shirt.
3. Enable Bitcoin test payments.
4. Complete an end-to-end test order.
5. Confirm Printful receives the correct product, size, color, address, and shipping method.
6. Verify customer emails and tracking updates.
7. Enable production credentials.
8. Place one real low-value order.
9. Launch the merchandise page.

## Deliverables

* Merchandise catalog page
* Product detail pages
* Cart and Bitcoin checkout
* Payment-status page
* Printful fulfillment integration
* Order and webhook database models
* Customer email notifications
* Admin order dashboard
* Setup documentation
* Environment-variable template
* Automated tests

Before writing code, summarize the current site architecture and propose the smallest-change implementation plan. Then implement the work incrementally, preserving existing functionality.
