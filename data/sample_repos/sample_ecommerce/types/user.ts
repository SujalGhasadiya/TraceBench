/**
 * User and customer profile data types.
 */

export interface UserProfile {
    id: string;
    email: string;
    username: string;
    role: 'customer' | 'admin' | 'vendor';
    createdAt: Date;
}

export interface AuthSession {
    token: string;
    expiresAt: number;
    user: UserProfile;
}
