// src/utils/passwordPolicy.js

export const passwordPolicy = {
    minLength: 12,
    requireUpper: true,
    requireLower: true,
    requireNumber: true,
    requireSpecial: true
}

export const validatePassword = (password) => {
    return {
        validLength: password.length >= passwordPolicy.minLength,
        hasUpper: /[A-Z]/.test(password),
        hasLower: /[a-z]/.test(password),
        hasNumber: /[0-9]/.test(password),
        hasSpecial: /[^A-Za-z0-9]/.test(password)
    }
}

export const isPasswordValid = (password) => {
    const v = validatePassword(password)

    return (
        v.validLength &&
        v.hasUpper &&
        v.hasLower &&
        v.hasNumber &&
        v.hasSpecial
    )
}