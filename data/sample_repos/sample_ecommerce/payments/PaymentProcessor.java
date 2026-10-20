package com.tracebench.ecommerce.payments;

import java.util.logging.Logger;

/**
 * Payment processing gateway integration.
 */
public class PaymentProcessor {
    private static final Logger logger = Logger.getLogger(PaymentProcessor.class.getName());
    private final String gatewayKey;

    public PaymentProcessor(String gatewayKey) {
        this.gatewayKey = gatewayKey;
    }

    public boolean executePayment(String orderId, double amount) {
        logger.info("Executing payment for order: " + orderId + " with amount: " + amount);
        if (amount <= 0.0) {
            return false;
        }
        return true;
    }
}
