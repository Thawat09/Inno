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

export function seedMockUsers() {
    const users = loadUsers()
    if (users.length > 0) return

    const seed = [
        {
            id: 1,
            email: 'user1@company.com',
            name: 'User One',
            role: 'employee',
            password: '',
            failedLoginCount: 0,
            isLocked: false,
            hasPassword: false
        },
        {
            id: 2,
            email: 'admin@company.com',
            name: 'Admin User',
            role: 'admin',
            password: 'Admin123!',
            failedLoginCount: 0,
            isLocked: false,
            hasPassword: true
        },
        {
            id: 3,
            email: 'superadmin@company.com',
            name: 'Super Admin',
            role: 'super_admin',
            password: 'Super123!',
            failedLoginCount: 0,
            isLocked: false,
            hasPassword: true
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

    if (!user) {
        return { ok: false, code: 'USER_NOT_FOUND', message: 'ไม่พบผู้ใช้งานในระบบ' }
    }

    if (user.isLocked) {
        return { ok: false, code: 'LOCKED', message: 'บัญชีถูกล็อก กรุณาติดต่อผู้ดูแลระบบ' }
    }

    if (!user.hasPassword || !user.password) {
        return {
            ok: false,
            code: 'PASSWORD_NOT_SET',
            message: 'ผู้ใช้นี้ยังไม่ได้ตั้งรหัสผ่าน',
            user
        }
    }

    if (user.password !== password) {
        user.failedLoginCount += 1

        if (user.failedLoginCount >= 3) {
            user.isLocked = true
        }

        saveUsers(users)

        return {
            ok: false,
            code: user.isLocked ? 'LOCKED' : 'INVALID_PASSWORD',
            message: user.isLocked
                ? 'กรอกรหัสผ่านผิดเกิน 3 ครั้ง บัญชีถูกล็อกแล้ว'
                : `รหัสผ่านไม่ถูกต้อง (ผิด ${user.failedLoginCount}/3)`
        }
    }

    user.failedLoginCount = 0
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
        return { ok: false, message: 'ไม่พบผู้ใช้งาน' }
    }

    if (user.isLocked) {
        return { ok: false, message: 'บัญชีถูกล็อก' }
    }

    user.password = password
    user.hasPassword = true
    user.failedLoginCount = 0

    saveUsers(users)

    return { ok: true, user }
}

export function generateOtp(email) {
    const user = findUserByEmail(email)
    if (!user) {
        return { ok: false, message: 'ไม่พบผู้ใช้งาน' }
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
        return { ok: false, message: 'ไม่พบ OTP กรุณากดส่งใหม่' }
    }

    if (Date.now() > record.expiresAt) {
        delete otpMap[key]
        saveOtpMap(otpMap)
        return { ok: false, message: 'OTP หมดอายุ กรุณากดส่งใหม่' }
    }

    if (String(record.code) !== String(otp)) {
        return { ok: false, message: 'OTP ไม่ถูกต้อง' }
    }

    delete otpMap[key]
    saveOtpMap(otpMap)

    const user = findUserByEmail(email)

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

    if (!user) return { ok: false, message: 'ไม่พบผู้ใช้' }

    user.isLocked = false
    user.failedLoginCount = 0

    saveUsers(users)
    return { ok: true }
}