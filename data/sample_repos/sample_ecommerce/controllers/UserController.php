<?php
namespace App\Controllers;

/**
 * Controller managing customer user accounts.
 */
class UserController {
    public function showProfile($userId) {
        $userData = [
            'id' => $userId,
            'status' => 'active',
            'role' => 'customer'
        ];
        return json_encode($userData);
    }

    public function updateEmail($userId, $newEmail) {
        return true;
    }
}
