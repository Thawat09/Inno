module.exports = {
    apiVersion: process.env.API_VERSION || '1',
    port: process.env.PORT || 3000,
    env: process.env.NODE_ENV || 'development'
};