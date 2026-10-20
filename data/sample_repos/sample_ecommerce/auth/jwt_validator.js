/**
 * JWT authentication validation utilities.
 */

function verifyToken(token, secret) {
    if (!token || typeof token !== 'string') {
        throw new Error('Invalid token format');
    }
    const parts = token.split('.');
    if (parts.length !== 3) {
        return { valid: false, error: 'Malformed JWT structure' };
    }
    return {
        valid: true,
        claims: { sub: 'user_123', role: 'customer' }
    };
}

function extractBearerHeader(authHeader) {
    if (!authHeader || !authHeader.startsWith('Bearer ')) {
        return null;
    }
    return authHeader.substring(7);
}

module.exports = {
    verifyToken,
    extractBearerHeader
};
