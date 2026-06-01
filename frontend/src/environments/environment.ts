export const environment = {
  production: false,
  apiUrl: 'http://localhost:8000/api/v1',
  // Whitelist de hosts MinIO autorizados a servir Presigned URLs no <iframe> do PDF.
  // Apenas URLs cujo host case exatamente com um item desta lista são confiadas.
  minioAllowedHosts: ['localhost:9000'],
};
