const USERS_KEY = 'mock_users'
const SESSION_KEY = 'mock_session'
const OTP_KEY = 'mock_otp'

function loadUsers() {
    return JSON.parse(localStorage.getItem(USERS_KEY) || '[]')
}

function saveUsers(users) {
    localStorage.setItem(USERS_KEY, JSON.stringify(users))
}

function loadOtpMap() {
    return JSON.parse(localStorage.getItem(OTP_KEY) || '{}')
}

function saveOtpMap(data) {
    localStorage.setItem(OTP_KEY, JSON.stringify(data))
}

function normalizeEmail(email) {
    return String(email || '').trim().toLowerCase()
}

function toRoleName(role) {
    switch (role) {
        case 'super_admin':
            return 'Super Admin'
        case 'admin':
            return 'Admin'
        case 'employee':
            return 'Employee'
        default:
            return 'User'
    }
}

export function seedMockUsers() {
    const users = loadUsers()
    if (users.length > 0) return

    const now = new Date().toISOString()

    const seed = [
        {
            id: 1,
            employee_code: 'EMP-0001',
            first_name: 'User',
            last_name: 'One',
            nickname: 'U1',
            phone: '0812345678',
            email: 'user1@company.com',
            name: 'User One',
            role: 'employee',
            role_name: 'Employee',
            main_team: 'Operations',
            sub_team: 'Standby',
            password: '',
            hasPassword: false,
            failedLoginCount: 0,
            isLocked: false,
            locked_at: '',
            last_login_at: '',
            is_active: true,
            created_at: now,
            updated_at: now
        },
        {
            id: 2,
            employee_code: 'EMP-0002',
            first_name: 'Admin',
            last_name: 'User',
            nickname: 'Admin',
            phone: '0899999999',
            email: 'admin@company.com',
            name: 'Admin User',
            role: 'admin',
            role_name: 'Admin',
            main_team: 'Infrastructure',
            sub_team: 'Cloud Operations',
            password: 'Admin123!',
            hasPassword: true,
            failedLoginCount: 0,
            isLocked: false,
            locked_at: '',
            last_login_at: '',
            is_active: true,
            created_at: now,
            updated_at: now
        },
        {
            id: 3,
            employee_code: 'EMP-0003',
            first_name: 'Super',
            last_name: 'Admin',
            nickname: 'SA',
            phone: '0888888888',
            email: 'superadmin@company.com',
            name: 'Super Admin',
            role: 'super_admin',
            role_name: 'Super Admin',
            main_team: 'Management',
            sub_team: 'Platform',
            password: 'Super123!',
            hasPassword: true,
            failedLoginCount: 0,
            isLocked: false,
            locked_at: '',
            last_login_at: '',
            is_active: true,
            created_at: now,
            updated_at: now
        }
    ]

    saveUsers(seed)
}

export function findUserByEmail(email) {
    const users = loadUsers()
    return users.find((u) => normalizeEmail(u.email) === normalizeEmail(email)) || null
}

export function loginWithPassword(email, password) {
    const users = loadUsers()
    const user = users.find((u) => normalizeEmail(u.email) === normalizeEmail(email))

    // ไม่ reveal ว่ามี user หรือไม่
    if (!user) {
        return {
            ok: false,
            code: 'USER_NOT_FOUND',
            message: 'Invalid email or password'
        }
    }

    // บอกเฉพาะกรณีโดน lock
    if (user.isLocked) {
        return {
            ok: false,
            code: 'LOCKED',
            message: 'This account has been locked due to multiple failed login attempts.'
        }
    }

    // first login flow
    if (!user.hasPassword || !user.password) {
        return {
            ok: false,
            code: 'PASSWORD_NOT_SET',
            message: 'Password has not been set',
            user
        }
    }

    // invalid password
    if (user.password !== password) {
        user.failedLoginCount += 1
        user.updated_at = new Date().toISOString()

        if (user.failedLoginCount >= 3) {
            user.isLocked = true
            user.locked_at = new Date().toISOString()
        }

        saveUsers(users)

        return {
            ok: false,
            code: user.isLocked ? 'LOCKED' : 'INVALID_PASSWORD',
            message: user.isLocked
                ? 'This account has been locked due to multiple failed login attempts.'
                : 'Invalid email or password'
        }
    }

    // success
    user.failedLoginCount = 0
    user.isLocked = false
    user.locked_at = ''
    user.last_login_at = new Date().toISOString()
    user.updated_at = new Date().toISOString()

    saveUsers(users)

    return {
        ok: true,
        code: 'PASSWORD_OK',
        user
    }
}

export function setFirstPassword(email, password) {
    const users = loadUsers()
    const user = users.find((u) => normalizeEmail(u.email) === normalizeEmail(email))

    if (!user) {
        return { ok: false, message: 'User not found' }
    }

    if (user.isLocked) {
        return { ok: false, message: 'This account is locked' }
    }

    user.password = password
    user.hasPassword = true
    user.failedLoginCount = 0
    user.isLocked = false
    user.locked_at = ''
    user.updated_at = new Date().toISOString()

    saveUsers(users)

    return { ok: true, user }
}

export function generateOtp(email) {
    const user = findUserByEmail(email)

    if (!user) {
        return { ok: false, message: 'Unable to generate OTP' }
    }

    if (user.isLocked) {
        return { ok: false, message: 'This account is locked' }
    }

    const otp = String(Math.floor(100000 + Math.random() * 900000))
    const otpMap = loadOtpMap()

    otpMap[normalizeEmail(email)] = {
        code: otp,
        expiresAt: Date.now() + 5 * 60 * 1000
    }

    saveOtpMap(otpMap)

    return {
        ok: true,
        otp,
        user
    }
}

export function verifyOtp(email, otp) {
    const key = normalizeEmail(email)
    const otpMap = loadOtpMap()
    const record = otpMap[key]

    if (!record) {
        return { ok: false, message: 'OTP not found. Please request a new one.' }
    }

    if (Date.now() > record.expiresAt) {
        delete otpMap[key]
        saveOtpMap(otpMap)
        return { ok: false, message: 'OTP expired. Please request a new one.' }
    }

    if (String(record.code) !== String(otp)) {
        return { ok: false, message: 'Invalid OTP' }
    }

    delete otpMap[key]
    saveOtpMap(otpMap)

    const user = findUserByEmail(email)

    if (!user) {
        return { ok: false, message: 'User not found' }
    }

    sessionStorage.setItem(
        SESSION_KEY,
        JSON.stringify({
            isAuthenticated: true,
            user
        })
    )

    return { ok: true, user }
}

export function getSession() {
    return JSON.parse(sessionStorage.getItem(SESSION_KEY) || 'null')
}

export function logout() {
    sessionStorage.removeItem(SESSION_KEY)
}

export function isAuthenticated() {
    const session = getSession()
    return !!session?.isAuthenticated
}

export function getCurrentUser() {
    const session = getSession()
    return session?.user || null
}

export function getLockedUsers() {
    return loadUsers().filter((u) => u.isLocked)
}

export function unlockUser(email) {
    const users = loadUsers()
    const user = users.find((u) => normalizeEmail(u.email) === normalizeEmail(email))

    if (!user) {
        return { ok: false, message: 'User not found' }
    }

    user.isLocked = false
    user.failedLoginCount = 0
    user.locked_at = ''
    user.updated_at = new Date().toISOString()

    saveUsers(users)
    return { ok: true }
}

export function updateCurrentUserProfile(payload) {
    const session = getSession()
    const currentUser = session?.user

    if (!currentUser?.email) {
        return { ok: false, message: 'Session not found' }
    }

    const users = loadUsers()
    const user = users.find((u) => normalizeEmail(u.email) === normalizeEmail(currentUser.email))

    if (!user) {
        return { ok: false, message: 'User not found' }
    }

    user.first_name = payload.first_name?.trim() || ''
    user.last_name = payload.last_name?.trim() || ''
    user.nickname = payload.nickname?.trim() || ''
    user.phone = payload.phone?.trim() || ''
    user.name = [user.first_name, user.last_name].filter(Boolean).join(' ') || user.email
    user.role_name = user.role_name || toRoleName(user.role)
    user.updated_at = new Date().toISOString()

    saveUsers(users)

    const updatedSession = {
        ...session,
        user: { ...user }
    }

    sessionStorage.setItem(SESSION_KEY, JSON.stringify(updatedSession))

    return { ok: true, user }
}

export function changePassword(email, currentPassword, newPassword) {
    const users = loadUsers()
    const user = users.find((u) => normalizeEmail(u.email) === normalizeEmail(email))

    if (!user) {
        return { ok: false, message: 'User not found' }
    }

    if (user.isLocked) {
        return {
            ok: false,
            message: 'This account has been locked due to multiple failed login attempts.'
        }
    }

    if (user.password !== currentPassword) {
        return {
            ok: false,
            message: 'Current password is incorrect'
        }
    }

    user.password = newPassword
    user.hasPassword = true
    user.updated_at = new Date().toISOString()

    saveUsers(users)

    const session = getSession()
    if (session?.user && normalizeEmail(session.user.email) === normalizeEmail(email)) {
        session.user = { ...user }
        sessionStorage.setItem(SESSION_KEY, JSON.stringify(session))
    }

    return { ok: true, user }
}

export function resetPassword(email, newPassword) {
    const users = loadUsers()
    const user = users.find(u => normalizeEmail(u.email) === normalizeEmail(email))

    if (!user) {
        return { ok: false, message: 'User not found' }
    }

    user.password = newPassword
    user.hasPassword = true
    user.failedLoginCount = 0
    user.isLocked = false
    user.locked_at = ''
    user.updated_at = new Date().toISOString()

    saveUsers(users)

    return { ok: true }
}