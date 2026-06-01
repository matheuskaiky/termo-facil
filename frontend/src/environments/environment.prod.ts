export const environment = {
  production: true,
  apiUrl: '/api/v1',
  // TODO(infra): preencher no deploy com o host real do MinIO / reverse-proxy
  // que serve as Presigned URLs (ex.: 'storage.ssp.pi.gov.br'). Lista vazia
  // rejeita todas as URLs por segurança até ser configurada.
  minioAllowedHosts: [] as string[],
};
