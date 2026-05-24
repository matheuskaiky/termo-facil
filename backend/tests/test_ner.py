import unittest
import sys
import os
import json

# Adiciona o diretório backend ao PYTHONPATH para poder importar app.services
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.ner_service import ner_model

# Transcrição simulando um depoimento real entre Escrivão e Vítima
TRANSCRICAO_BASE = """[00:00:00] Escrivão Roberto: Bom dia, senhora. Pode entrar, por favor. Sente-se aqui nessa cadeira. Meu nome é Roberto, sou escrivão aqui na 3ª Delegacia de Polícia de São Paulo. A senhora está muito pálida, aceita um copo d'água antes de começarmos?
[00:00:15] Vítima Mariana: [Voz trêmula] Bom dia... Aceito sim, por favor. Eu ainda estou um pouco nervosa, vim direto pra cá.
[00:00:22] Escrivão Roberto: Fique tranquila. O pior já passou, a senhora está segura aqui. [Som de água sendo servida]. Pode tomar com calma. [Pausa de 10 segundos]. Quando a senhora se sentir pronta, eu vou pedir que me informe seu nome completo para a gente iniciar o registro no sistema, tá bom?
[00:00:40] Vítima Mariana: Obrigada. [Suspiro]. Meu nome é Mariana Costa Santos. Eu vim registrar um boletim de ocorrência porque fui assaltada hoje de manhã.
[00:00:52] Escrivão Roberto: Certo, Dona Mariana. Antes de entrarmos nos detalhes do assalto, eu preciso preencher a sua qualificação. Qual a sua data de nascimento, estado civil e profissão?
[00:01:05] Vítima Mariana: Eu nasci no dia 14 de maio de 1992. Sou solteira. E trabalho como analista financeira no Banco Itaú.
[00:01:15] Escrivão Roberto: [Som de digitação]. Analista financeira... Banco Itaú. A senhora sabe de cabeça o número do seu RG e CPF, ou eles foram levados junto na bolsa?
[00:01:28] Vítima Mariana: Foram levados, infelizmente. Mas eu tenho uma foto deles aqui no sistema de nuvem do meu relógio. Só um instante... [Pausa]. O CPF é 345... 882... 198, dígito 44. O RG é 42... 981... 332, dígito X.
[00:01:55] Escrivão Roberto: [Som de digitação lenta]. 332, dígito X. São Paulo, correto? Ok. Qual o seu endereço residencial completo, com CEP, por favor?
[00:02:08] Vítima Mariana: Rua das Acácias, número 142, apartamento 51. Fica no bairro de Pinheiros. O CEP é 05423-000.
[00:02:22] Escrivão Roberto: [Som de digitação]. Apartamento 51... Pinheiros. Excelente. Agora sim, Dona Mariana, vamos ao fato. Tente lembrar com calma. Onde exatamente isso ocorreu e a que horas a senhora estima que foi?
[00:02:40] Vítima Mariana: Foi na Avenida Brigadeiro Faria Lima, bem pertinho do cruzamento com a Rua Juscelino Kubitschek. Eu olho sempre o relógio no caminho, então tenho certeza absoluta de que foi por volta das 08:30 da manhã. Eu estava indo a pé para a agência onde trabalho.
[00:03:00] Escrivão Roberto: Entendi. [Digitando]. O local estava muito movimentado nessa hora? Como foi a abordagem dele? Ele falou alguma coisa?
[00:03:12] Vítima Mariana: Olha, a avenida tinha bastante trânsito de carros, mas na calçada onde eu estava, naquele momento exato, não tinha muita gente. Ele simplesmente atravessou a rua, veio andando muito rápido na minha direção, me prensou contra o muro de um prédio comercial e disse: "Passa a bolsa, não grita senão eu atiro".
[00:03:35] Escrivão Roberto: Ele chegou a encostar na senhora com violência? Puxou o seu cabelo, a empurrou?
[00:03:42] Vítima Mariana: Não, bater não bateu, mas ele puxou a alça da minha bolsa com muita força, chegou a raspar meu ombro, tá até vermelho aqui. E, nessa hora, ele levantou a camisa pra mostrar a arma.
[00:04:00] Escrivão Roberto: Entendo. A senhora mencionou a arma. Conseguiu ver bem? Sabe diferenciar se era um revólver, daqueles que têm um tambor redondinho no meio, ou uma pistola, que é mais reta e quadrada?
[00:04:15] Vítima Mariana: Era um revólver. Sim, tinha aquele tambor. Parecia de metal bem escuro, meio velho, desgastado, sabe? Ele não chegou a apontar pra minha cabeça, ficou com a mão no cabo, dentro da calça.
[00:04:35] Escrivão Roberto: [Digitando]. Revólver escuro... Certo. Vamos falar sobre o suspeito agora. Preciso da melhor descrição física que a senhora conseguir se lembrar. Começando pela altura, cor da pele, idade aparente...
[00:04:52] Vítima Mariana: Ele era alto, bem mais alto que eu, acho que um metro e oitenta e cinco. Era magro, mas não raquítico, tinha ombros largos. Ele era pardo, o cabelo estava bem raspado nas laterais e um pouco maior em cima.
[00:05:12] Escrivão Roberto: Lembra de alguma cicatriz, piercing, ou tatuagem que chame a atenção?
[00:05:18] Vítima Mariana: Sim! Tinha uma tatuagem no pescoço, do lado direito.
[00:05:25] Escrivão Roberto: Tatuagem no pescoço? Lembra do desenho ou do formato?
[00:05:30] Vítima Mariana: Parecia uma teia de aranha, ou algo com linhas pretas grossas descendo pela garganta. Eu fiquei muito nervosa olhando para a arma, mas essa tatuagem marcou muito. Ele aparentava ter uns 25 a 30 anos.
[00:05:48] Escrivão Roberto: Ótimo, Dona Mariana. Esse detalhe da teia de aranha é crucial, ajuda muito o setor de investigação a filtrar suspeitos. Sobre as roupas, a senhora disse que ele vestia uma jaqueta preta. Lembra de mais alguma peça?
[00:06:05] Vítima Mariana: Isso. Era uma jaqueta preta daquelas de náilon, meio bufante. Usava uma calça jeans bem desbotada, meio rasgada no joelho, e um tênis vermelho.
[00:06:20] Escrivão Roberto: [Digitando]. Jaqueta preta, calça desbotada, tênis vermelho... Ok. Agora, a fuga. Como foi? Ele saiu correndo a pé?
[00:06:35] Vítima Mariana: Ele arrancou a bolsa do meu ombro, virou as costas e saiu andando rápido, quase correndo, em direção à Estação Pinheiros. Mas ele não foi longe a pé. Logo ali na frente, ele entrou em um carro que estava parado com o pisca-alerta ligado, bem em frente à farmácia Droga Raia.
[00:06:55] Escrivão Roberto: O carro era o Fiat Uno que a senhora comentou quando chegou. Lembra da cor? Havia outra pessoa dirigindo? Conseguiu ver a placa?
[00:07:08] Vítima Mariana: Era um Fiat Uno prata. Modelo mais antigo, aqueles bem quadrados. Tinha um comparsa dirigindo sim, porque o assaltante abriu a porta do passageiro, jogou a bolsa e entrou. O carro arrancou na mesma hora cantando pneu. Da placa, eu fiquei repetindo na cabeça pra não esquecer, mas só peguei as letras: era "E" de escola, "Q" de queijo e "S" de sapato. EQS. Os números eu não vi.
[00:07:38] Escrivão Roberto: [Som de digitação rápida]. Perfeito. Placa inicial EQS, Fiat Uno Prata. Concurso de pessoas configurado. Vou registrar tudo isso. Agora vamos fazer o levantamento do que foi subtraído. A senhora disse que levaram a bolsa. Como ela era e o que exatamente tinha dentro?
[00:08:00] Vítima Mariana: Era uma bolsa de couro sintético marrom, tamanho médio, com alça de ombro. Dentro estava o meu celular...
[00:08:10] Escrivão Roberto: Qual a marca, modelo e cor do aparelho?
[00:08:14] Vítima Mariana: É um iPhone 13, de cor branca. Estava com uma capinha de silicone transparente.
[00:08:22] Escrivão Roberto: A senhora tem o número do IMEI dele anotado em casa ou na caixa do aparelho? É fundamental para pedirmos o bloqueio junto à operadora para inutilizar o telefone.
[00:08:34] Vítima Mariana: A caixa está na gaveta do meu quarto, eu posso ligar pra minha mãe procurar agora se o senhor precisar.
[00:08:40] Escrivão Roberto: Não precisa se apressar agora, a senhora pode trazer ou ligar mais tarde para adicionarmos o número ao BO num aditamento. Além do celular, o que mais estava lá?
[00:08:52] Vítima Mariana: Minha carteira com meus documentos originais: RG, CNH, título de eleitor. Dois cartões de crédito, um do Itaú e um do Nubank. Tinha também meu crachá do banco, minhas chaves de casa e um fone de ouvido da Apple.
[00:09:12] Escrivão Roberto: A senhora já entrou em contato com os bancos para cancelar os cartões?
[00:09:18] Vítima Mariana: Sim, eu entrei na farmácia logo depois, pedi o telefone fixo deles emprestado e já liguei bloqueando tudo. Graças a Deus, pelo aplicativo do Nubank que vi pelo computador da farmácia, não deu tempo de passarem nada.
[00:09:35] Escrivão Roberto: Agiu muito bem, a rapidez nessas horas evita um prejuízo maior. Bom, o fato será tipificado no Artigo 157 do Código Penal, Roubo Qualificado pelo concurso de pessoas e emprego de arma de fogo. Dona Mariana, a senhora percebeu se a Droga Raia ou os prédios em volta têm câmeras de segurança voltadas para a calçada?
[00:09:58] Vítima Mariana: Tem sim. A Droga Raia tem uma câmera bem em cima da porta de entrada, que com certeza filmou o carro estacionado. E o muro do prédio onde fui abordada tem aquelas câmeras redondinhas pretas apontadas direto pra rua. Devem ter pego tudo.
[00:10:15] Escrivão Roberto: Excelente. O delegado vai expedir uma ordem de requisição de imagens para esses dois locais. Eu vou imprimir o Boletim de Ocorrência agora. [Som prolongado de digitação e clique de mouse. Barulho de impressora ao fundo].
[00:10:38] Escrivão Roberto: Aqui está. Eu peço que a senhora leia com muita atenção, veja se o seu nome, CPF e o relato do roubo estão de acordo com o que conversamos. Se precisar mudar uma vírgula, a senhora me avisa.
[00:10:55] Vítima Mariana: [Pausa longa para leitura] ... Sim... A rua está certa, a placa EQS, a descrição da tatuagem... Está tudo certinho, seu Roberto.
[00:11:15] Escrivão Roberto: Certo. Pode assinar no final dessa folha e rubricar a primeira, por favor. O sistema já gerou o número do seu BO ali no cabeçalho. Com essa via, a senhora já consegue solicitar a segunda via dos seus documentos no Poupatempo.
[00:11:32] Vítima Mariana: [Som de caneta no papel]. Pronto. Muito obrigada pela paciência e por ter me acalmado.
[00:11:40] Escrivão Roberto: Por nada, Dona Mariana. É o nosso dever. Qualquer novidade sobre a placa do carro ou imagens da farmácia, a equipe de investigação entrará em contato pelos telefones que a senhora forneceu. Vá com segurança para casa e tente descansar."""

TRANSCRICAO_LONGA = TRANSCRICAO_BASE * 15  # Multiplicando para garantir > 512 tokens

class TestNERExtraction(unittest.TestCase):
    def test_extracao_entidades_texto_longo(self):
        """
        Testa a extração de entidades nomeadas em um texto longo simulando um depoimento.
        Imprime as entidades encontradas para que você possa inspecionar o resultado.
        """
        print("\n" + "="*50)
        print("INICIANDO EXTRAÇÃO DE ENTIDADES (PODE LEVAR ALGUNS SEGUNDOS)")
        print("="*50)
        
        resultado = ner_model.extract_entities(TRANSCRICAO_LONGA)
        
        print("\n=== ENTIDADES EXTRAÍDAS PELO MODELO ===")
        # Imprime o resultado formatado no terminal
        print(json.dumps(resultado, indent=4, ensure_ascii=False))
        print("=======================================\n")
        
        # Verifica se o resultado contém as chaves esperadas
        chaves_esperadas = ["PESSOAS", "LOCAIS", "ORGANIZACOES", "TEMPO", "LEGISLACAO", "JURISPRUDENCIA"]
        for chave in chaves_esperadas:
            self.assertIn(chave, resultado)
            
        # Verifica se entidades foram extraídas com sucesso
        self.assertGreater(len(resultado["PESSOAS"]), 0, "Deveria ter encontrado pessoas.")
        self.assertGreater(len(resultado["LOCAIS"]), 0, "Deveria ter encontrado locais.")
        self.assertGreater(len(resultado["ORGANIZACOES"]), 0, "Deveria ter encontrado organizações.")

if __name__ == '__main__':
    unittest.main()
