# Aula 02-09 - Produtor-Consumidor

## Descrição

Implementação de um sistema distribuído estilo produtor-consumidor. Dois serviços em linguagens diferentes produzem eventos que serão consumidos por dois outros serviços.

Nos serviços produtores é possível consultar a quantidade de eventos criados, buscar o valor de um evento específico e criar eventos sincronamente, aguardando um processamento, e assincronamente, retornando imediatamente o id do evento criado para consulta posterior.

## Componentes

- [Banco de dados MySQL](#banco-de-dados-mysql)
- [Serviço backend em Python](#serviços-backend-em-python-e-nodejs)
- [Serviço backend em Node.js](#serviços-backend-em-python-e-nodejs)
- [Consumidor de eventos em Python](#consumidores-de-eventos-em-python-e-go)
- [Consumidor de eventos em Go](#consumidores-de-eventos-em-python-e-go)
- [Balanceador de carga Nginx](#balanceador-de-carga-nginx)

### Banco de dados MySQL

Armazena um status geral e os eventos criados pelos serviços backend.

Para isso, possui duas tabelas:

- `DBStatus`:
  - `id INT`: contador do número de eventos da aplicação
- `Events`:
  - `id INT`: número identificador do evento
  - `valor VARCHAR`: palavra que será adicionada pelo consumidor. Por padrão o valor é `NULL` ou string vazia `''`.
  - `processing INT`: valor que indica se a linha está sendo processada/travada (`1`) ou não/livre (`0`)

A definição do banco de dados está disponível no arquivo [`init.sql`](./database/init.sql).

### Serviços backend em Python e Node.js

Cada um deles expõe uma API ReST com os mesmo endpoints para consulta e criação de eventos sincronamente ou assincronamente.

Eles são os responsáveis por produzir os eventos que serão armazenados no banco de dados MySQL.

Ambos os serviços possuem os mesmos _endpoints_:

- `/`: retorna a quantidade de eventos criados
- `/{id}`: retorna o valor de um evento especificado pelo parâmetro `id`.
- `/create-sync`: cria um novo evento sincronamente. Ou seja, só obterá uma resposta à requisição quando o evento for consumido e um valor (palavra) for adicionado(a). Será realizada uma verificação do processamento do evento a cada 100ms, sem número máximo de tentativas.
- `/create-sync`: cria um novo evento assincronamente. Ou seja, obterá uma resposta imediatamente com o número identificador do evento criado. O evento será consumido quando possível e um valor (palavra) for adicionado(a).

São dois produtores:

- [Node.js](./app-js/)
- [Python](./app-python/)

### Consumidores de eventos em Python e Go

São serviços que consomem e processam os eventos criados, adicionando um valor, o qual é o retorno de uma chamada para busca de uma palavra da lingua portuguesa.

Quando um novo evento é criado, este é travado (_locked_) pelo primeiro consumidor com a intenção de processá-lo. Isso ocorre por meio da coluna `processing`. Após processado, o evento é destravado.

São dois consumidores:

- [Go](./consumer-go/)
- [Python](./consumer-python/)

### Balanceador de carga Nginx

É utilizado um balanceador de carga para dividir o fluxo de entrada entre os serviços produtores de evento.

Foi utilizado o servidor web e proxy reverso Nginx para realizar o balanceamento de carga. Por padrão, o Nginx utiliza a técnica _round-robin_ para dividir o fluxo de entrada igualmente entre os servidores.

A configuração do Nginx para balanceamento de carga está definida no arquivo [`nginx.conf`](./nginx/nginx.conf)

## Setup e execução

Foi utilizado o [Docker](./docker-compose.yaml) para subir os componentes sistema de forma automática.

No arquivo [`docker-compose.yaml`](./docker-compose.yaml) são definidos os serviços e as configurações de cada. Para cada um dos serviços, há um arquivo `Dockerfile` para criação de uma imagem customizada, a fim de subir o componente e executar corretamente o serviço.

Portanto, para executar a aplicação, basta seguir os seguintes passos:

1. Subir containers:

Com o comando abaixo, será executada a configuração definida no arquivo `docker-compose.yaml`, garantindo a ordem a seguir.

1. MySQL
2. Produtores Node.js e Python
3. Balanceador de carga

```bash
docker compose up --build
```

> Pode ser utilizada a flag `-d` para executar os containers em background.

2. Executar consumidores:

Os consumidores não serão executados juntamente com os outros serviços para ser possível visualizar os logs de processamento.

1. Python:

> É necessário possuir suporte à linguagem Python na sua máquina.

Entrar na pasta e ativar o ambiente virtual Python:

```bash
cd consumer-python && source ./venv/bin/activate
```

Instalar dependências:

```bash
pip install -r requirements.txt
```

Executar consumidor:

```bash
python app.py
```

2. Go:

> É necessário possuir suporte à linguagem Go na sua máquina.

Entrar na pasta do consumidor:

```bash
cd consumer-go
```

Instalar dependências:

```bash
go get
```

Executar consumidor:

```bash
go build -o app.exe app.go && ./app.exe
```

ou

```bash
go run app.go
```
