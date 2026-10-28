import math
import unicodedata


class EntradaEncerrada(Exception):
    """Indica que o usuário encerrou a entrada de dados (EOF)."""


def nome_valido(nome):
    """Aceita nomes com letras, espaços e poucos sinais; nunca números."""
    if not isinstance(nome, str):
        return False
    nome = nome.strip()
    if not nome or not any(caractere.isalpha() for caractere in nome):
        return False
    if any(caractere.isdigit() for caractere in nome):
        return False
    return all(caractere.isalpha() or caractere in " .'-&" for caractere in nome)


def normalizar_texto(texto):
    """Remove acentos e diferenças de maiúsculas para comparações simples."""
    texto = unicodedata.normalize("NFKD", str(texto).strip().lower())
    return "".join(caractere for caractere in texto if not unicodedata.combining(caractere))


def ler_entrada(mensagem):
    """Lê uma entrada e encerra o programa de forma amigável se o usuário usar EOF."""
    try:
        return input(mensagem)
    except EOFError as erro:
        raise EntradaEncerrada from erro


class Produto:
    def __init__(self, nome, categoria, preco, quantidade):
        self.nome = nome
        self.categoria = categoria  # "fresco" ou "congelado"
        self.preco = preco
        self.quantidade = quantidade
        self.empresa = None
        self.foto = None  # opcional

    def verificar_disponibilidade(self, quantidade_solicitada):
        # Produto com estoque zero continua cadastrado, mas indisponível
        if (not isinstance(quantidade_solicitada, (int, float))
                or isinstance(quantidade_solicitada, bool)
                or not math.isfinite(quantidade_solicitada)):
            return False
        if self.quantidade <= 0:
            return False
        return self.quantidade >= quantidade_solicitada

    def atualizar_quantidade(self, nova_quantidade):
        # Quantidade não pode ficar negativa; produto fica indisponível ao chegar a zero
        if (not isinstance(nova_quantidade, (int, float))
                or isinstance(nova_quantidade, bool)
                or not math.isfinite(nova_quantidade)):
            return False
        self.quantidade = max(0, nova_quantidade)
        return True


class ItemPedido:
    def __init__(self, produto, quantidade):
        self.produto = produto
        self.quantidade = quantidade
        self.preco_unitario = produto.preco


class Pedido:
    def __init__(self, empresa_compradora, endereco_entrega, tempo_entrega):
        self.empresa_compradora = empresa_compradora
        self.endereco_entrega = endereco_entrega
        self.tempo_entrega = tempo_entrega
        self.itens = []
        self.empresa_marisqueira = None
        self.status = "Pendente"
        self.status_entrega = "Não iniciada"

    def adicionar_item(self, produto, quantidade):
        if not isinstance(produto, Produto):
            print("Erro: Produto inválido.")
            return False
        if produto.empresa is None:
            print("Erro: Produto não está cadastrado em uma empresa marisqueira.")
            return False

        if self.status not in ("Pendente", "Ajuste Solicitado"):
            print(f"Erro: Não é possível adicionar itens a um pedido com status '{self.status}'.")
            return False

        if not self.validar_quantidade(quantidade):
            print(f"Erro: Quantidade mínima não atendida para '{produto.nome}'. Mínimo é 25kg.")
            return False

        quantidade_ja_pedida = 0
        item_existente = None
        for item in self.itens:
            if item.produto == produto:
                quantidade_ja_pedida = item.quantidade
                item_existente = item
                break

        quantidade_total = quantidade_ja_pedida + quantidade
        if produto.quantidade < quantidade_total:
            print(f"Erro: Estoque insuficiente para '{produto.nome}'. "
                  f"Disponível: {produto.quantidade}kg, total solicitado: {quantidade_total}kg.")
            return False

        if self.empresa_marisqueira is None:
            self.empresa_marisqueira = produto.empresa
        elif self.empresa_marisqueira != produto.empresa:
            print("Erro: Não é permitido misturar produtos de empresas marisqueiras diferentes no mesmo pedido.")
            return False

        if item_existente:
            item_existente.quantidade += quantidade
            print(f"Atualizado: '{produto.nome}' agora tem {item_existente.quantidade}kg no pedido.")
        else:
            item = ItemPedido(produto, quantidade)
            self.itens.append(item)
            print(f"Adicionado: {quantidade}kg de '{produto.nome}' ao pedido.")
        return True

    def validar_quantidade(self, quantidade):
        return (isinstance(quantidade, (int, float))
                and not isinstance(quantidade, bool)
                and math.isfinite(quantidade)
                and quantidade >= 25)

    def verificar_disponibilidade(self, produto, quantidade):
        if not isinstance(produto, Produto):
            return False
        return produto.verificar_disponibilidade(quantidade)


class Avaliacao:
    def __init__(self, empresa_compradora):
        self.empresa_compradora = empresa_compradora
        self.nota = 0

    def registrar_nota(self, nota):
        if isinstance(nota, bool) or not isinstance(nota, int):
            print(f"Erro: Nota inválida ({nota}). A avaliação deve ser um número inteiro entre 1 e 5.")
            return False
        if 1 <= nota <= 5:
            self.nota = nota
            return True
        else:
            print(f"Erro: Nota inválida ({nota}). A avaliação deve ser entre 1 e 5 estrelas.")
            return False


class Empresa:
    def __init__(self, nome, localizacao):
        self.nome = nome
        self.localizacao = localizacao


class EmpresaMarisqueira(Empresa):
    LIMITE_ESTOQUE_BAIXO = 50
    STATUS_ENTREGA_VALIDOS = ("Em preparação", "Em trânsito", "Entregue")

    def __init__(self, nome, localizacao):
        super().__init__(nome, localizacao)
        self.produtos = []
        self.pedidos = []
        self.avaliacoes = []

    def obter_status_visual(self, em_horario_funcionamento=True):
        if not em_horario_funcionamento:
            return "Vermelho (Fora do horário)"
        estoque_total = sum(p.quantidade for p in self.produtos)
        if estoque_total == 0:
            return "Vermelho (Sem estoque)"
        elif estoque_total < EmpresaMarisqueira.LIMITE_ESTOQUE_BAIXO:
            return "Laranja (Estoque baixo)"
        else:
            return "Verde (Disponível)"

    def cadastrar_produto(self, produto):
        if not isinstance(produto, Produto):
            print("Erro: Produto inválido.")
            return False
        if produto in self.produtos:
            print(f"Erro: O produto '{produto.nome}' já está cadastrado nesta empresa.")
            return False
        if produto.empresa is not None and produto.empresa is not self:
            print(f"Erro: O produto '{produto.nome}' já pertence a outra empresa.")
            return False
        if not nome_valido(produto.nome):
            print("Erro: Nome do produto inválido. Use apenas letras, espaços, ponto, "
                  "hífen, apóstrofo ou & (sem números).")
            return False
        produto.nome = " ".join(produto.nome.split())
        produto.categoria = str(produto.categoria).strip().lower()
        if produto.categoria not in ("fresco", "congelado"):
            print(f"Erro: Categoria '{produto.categoria}' inválida. Use 'fresco' ou 'congelado'.")
            return False
        if (not isinstance(produto.preco, (int, float))
                or isinstance(produto.preco, bool)
                or not math.isfinite(produto.preco)):
            print("Erro: Preço deve ser um número válido.")
            return False
        if (not isinstance(produto.quantidade, (int, float))
                or isinstance(produto.quantidade, bool)
                or not math.isfinite(produto.quantidade)):
            print("Erro: Quantidade deve ser um número válido.")
            return False
        if produto.preco <= 0:
            print("Erro: Preço deve ser maior que zero.")
            return False
        if produto.quantidade < 25:
            print("Erro: Quantidade mínima para cadastro é 25kg.")
            return False
        self.produtos.append(produto)
        produto.empresa = self
        print(f"[{self.nome}] Produto '{produto.nome}' cadastrado.")
        return True

    def alterar_quantidade(self, produto, nova_quantidade):
        if not isinstance(produto, Produto):
            print("Erro: Produto inválido.")
            return False
        if produto not in self.produtos:
            print(f"Erro: Produto '{produto.nome}' não pertence a esta empresa.")
            return False
        if (not isinstance(nova_quantidade, (int, float))
                or isinstance(nova_quantidade, bool)
                or not math.isfinite(nova_quantidade)):
            print("Erro: Quantidade inválida. Nenhuma alteração feita.")
            return False
        if nova_quantidade < 0:
            print("Erro: Quantidade não pode ser negativa. Nenhuma alteração feita.")
            return False
        produto.atualizar_quantidade(nova_quantidade)
        print(f"[{self.nome}] Quantidade de '{produto.nome}' atualizada para {produto.quantidade}kg.")
        return True

    def receber_pedido(self, pedido):
        if pedido.empresa_marisqueira != self:
            print(f"Erro: Este pedido não pertence a '{self.nome}'.")
            return False
        if len(pedido.itens) == 0:
            print("Erro: Não é possível receber um pedido sem itens.")
            return False
        if pedido.status != "Pendente":
            print(f"Erro: Pedido deve estar 'Pendente' para ser recebido. Status atual: '{pedido.status}'.")
            return False
        self.pedidos.append(pedido)
        pedido.status = "Recebido"
        print(f"[{self.nome}] Pedido recebido.")
        return True

    def aceitar_pedido(self, pedido):
        if pedido.empresa_marisqueira != self:
            print(f"Erro: Este pedido não pertence a '{self.nome}'.")
            return False
        if pedido.status not in ("Recebido", "Ajuste Solicitado"):
            print(f"Erro: Pedido não pode ser aceito. Status atual: '{pedido.status}'.")
            return False
        # Re-verifica estoque para todos os itens antes de descontar
        for item in pedido.itens:
            if item.produto.quantidade < item.quantidade:
                print(f"Erro: Estoque insuficiente para '{item.produto.nome}'. "
                      f"Disponível: {item.produto.quantidade}kg, solicitado: {item.quantidade}kg.")
                pedido.status = "Rejeitado"
                print(f"[{self.nome}] Pedido rejeitado por falta de estoque.")
                return False
        for item in pedido.itens:
            item.produto.atualizar_quantidade(item.produto.quantidade - item.quantidade)
        pedido.status = "Aceito"
        print(f"[{self.nome}] Pedido aceito. Estoque atualizado.")
        return True

    def rejeitar_pedido(self, pedido):
        if pedido.empresa_marisqueira != self:
            print(f"Erro: Este pedido não pertence a '{self.nome}'.")
            return False
        if pedido.status == "Aceito":
            print("Erro: Não é possível rejeitar um pedido já aceito.")
            return False
        pedido.status = "Rejeitado"
        print(f"[{self.nome}] Pedido rejeitado.")
        return True

    def solicitar_ajuste(self, pedido):
        if pedido.empresa_marisqueira != self:
            print(f"Erro: Este pedido não pertence a '{self.nome}'.")
            return False
        if pedido.status == "Aceito":
            print("Erro: Não é possível solicitar ajuste em um pedido já aceito.")
            return False
        pedido.status = "Ajuste Solicitado"
        print(f"[{self.nome}] Ajuste solicitado para o pedido.")
        return True

    def atualizar_status_entrega(self, pedido, status):
        if pedido.status != "Aceito":
            print(f"Erro: Só é possível atualizar a entrega de um pedido aceito. Status atual: '{pedido.status}'.")
            return False
        status_por_nome = {normalizar_texto(opcao): opcao for opcao in self.STATUS_ENTREGA_VALIDOS}
        status_normalizado = status_por_nome.get(normalizar_texto(status))
        if status_normalizado is None:
            print("Erro: Status de entrega inválido. Use: Em preparação, Em trânsito ou Entregue.")
            return False
        pedido.status_entrega = status_normalizado
        print(f"[{self.nome}] Status da entrega atualizado para: '{status_normalizado}'.")
        return True

    def media_avaliacoes(self):
        if not self.avaliacoes:
            return 0
        return sum(a.nota for a in self.avaliacoes) / len(self.avaliacoes)


class EmpresaCompradora(Empresa):
    def __init__(self, nome, localizacao):
        super().__init__(nome, localizacao)

    def consultar_produtos(self, todos_produtos, filtro_nome=None, filtro_categoria=None,
                           filtro_localizacao=None, filtro_empresa=None,
                           filtro_avaliacao=None, ordenar_por=None):
        resultados = []
        for p in todos_produtos:
            if not isinstance(p, Produto):
                continue
            if filtro_nome and filtro_nome.lower() not in p.nome.lower():
                continue
            if filtro_categoria and filtro_categoria.lower() != p.categoria.lower():
                continue
            if filtro_localizacao:
                if p.empresa is None or filtro_localizacao.lower() not in p.empresa.localizacao.lower():
                    continue
            if filtro_empresa:
                if p.empresa is None or filtro_empresa.lower() not in p.empresa.nome.lower():
                    continue
            if filtro_avaliacao:
                if p.empresa is None or p.empresa.media_avaliacoes() < filtro_avaliacao:
                    continue
            resultados.append(p)

        # Ordenação
        if ordenar_por == "menor_preco":
            resultados.sort(key=lambda p: p.preco)
        elif ordenar_por == "maior_preco":
            resultados.sort(key=lambda p: p.preco, reverse=True)
        elif ordenar_por == "melhor_avaliacao":
            resultados.sort(key=lambda p: p.empresa.media_avaliacoes(), reverse=True)
        elif ordenar_por == "localizacao":
            resultados.sort(key=lambda p: p.empresa.localizacao)

        return resultados

    def comparar_produtos(self, produto1, produto2):
        aval1 = f"{produto1.empresa.media_avaliacoes():.1f}" if produto1.empresa.avaliacoes else "Sem avaliação"
        aval2 = f"{produto2.empresa.media_avaliacoes():.1f}" if produto2.empresa.avaliacoes else "Sem avaliação"
        comparacao = (
            f"--- Comparação de Produtos ---\n"
            f"{'Atributo':<20} {'Produto 1':<20} {'Produto 2':<20}\n"
            f"{'Nome':<20} {produto1.nome:<20} {produto2.nome:<20}\n"
            f"{'Categoria':<20} {produto1.categoria:<20} {produto2.categoria:<20}\n"
            f"{'Preço (kg)':<20} R${produto1.preco:<18.2f} R${produto2.preco:<18.2f}\n"
            f"{'Disponível (kg)':<20} {produto1.quantidade:<20} {produto2.quantidade:<20}\n"
            f"{'Empresa':<20} {produto1.empresa.nome:<20} {produto2.empresa.nome:<20}\n"
            f"{'Avaliação':<20} {aval1:<20} {aval2:<20}"
        )
        return comparacao

    def realizar_pedido(self, endereco_entrega, tempo_entrega):
        if not isinstance(endereco_entrega, str) or not endereco_entrega.strip():
            print("Erro: Endereço de entrega não pode ser vazio.")
            return None
        if not isinstance(tempo_entrega, str) or not tempo_entrega.strip():
            print("Erro: Tempo de entrega não pode ser vazio.")
            return None
        return Pedido(self, endereco_entrega.strip(), tempo_entrega.strip())

    def avaliar_empresa(self, empresa_marisqueira, nota):
        if not isinstance(empresa_marisqueira, EmpresaMarisqueira):
            print("Erro: Empresa marisqueira inválida para avaliação.")
            return False
        tem_compra = False
        for pedido in empresa_marisqueira.pedidos:
            if pedido.empresa_compradora == self and pedido.status == "Aceito":
                tem_compra = True
                break
        if not tem_compra:
            print(f"Erro: [{self.nome}] só pode avaliar '{empresa_marisqueira.nome}' após ter uma compra aceita.")
            return False
        avaliacao = Avaliacao(self)
        if avaliacao.registrar_nota(nota):
            empresa_marisqueira.avaliacoes.append(avaliacao)
            print(f"[{self.nome}] Avaliou '{empresa_marisqueira.nome}' com {nota} estrela(s).")
            return True
        return False





# ============================================================
#  MENU INTERATIVO NO TERMINAL
# ============================================================

marisqueiras_cadastradas = []
compradoras_cadastradas  = []
pedidos_cadastrados      = []
dados_demo_carregados    = False


def linha():
    print("─" * 55)


def titulo(texto):
    print(f"\n{'=' * 55}")
    print(f"  {texto}")
    print(f"{'=' * 55}")


def ler_texto(mensagem):
    """Lê um texto obrigatório (pode conter números, útil para endereços)."""
    while True:
        texto = " ".join(ler_entrada(mensagem).split())
        if texto:
            return texto
        print("  [!] Este campo não pode ficar vazio.")


def ler_texto_opcional(mensagem):
    texto = " ".join(ler_entrada(mensagem).split())
    return texto or None


def ler_nome(mensagem):
    """Lê um nome sem números e sem símbolos estranhos."""
    while True:
        nome = " ".join(ler_entrada(mensagem).split())
        if not nome:
            print("  [!] O nome não pode ficar vazio.")
            continue
        if any(caractere.isdigit() for caractere in nome):
            print("  [!] O nome não pode conter números. Use apenas letras.")
            continue
        if not nome_valido(nome):
            print("  [!] Nome inválido. Use apenas letras, espaços, ponto, hífen, apóstrofo ou &.")
            continue
        return nome


def ler_opcao(mensagem, opcoes, permitir_vazio=False):
    """Repete a pergunta até o usuário digitar uma opção válida."""
    if isinstance(opcoes, dict):
        mapa = {str(chave).strip().lower(): valor for chave, valor in opcoes.items()}
        exemplos = " | ".join(str(chave) for chave in opcoes)
    else:
        mapa = {str(opcao).strip().lower(): opcao for opcao in opcoes}
        exemplos = " | ".join(str(opcao) for opcao in opcoes)

    while True:
        valor = ler_entrada(mensagem).strip()
        if permitir_vazio and not valor:
            return None
        escolha = mapa.get(valor.lower())
        if escolha is not None:
            return escolha
        print(f"  [!] Opção inválida. Opções válidas: {exemplos}.")


def ler_inteiro(mensagem, minimo=None, maximo=None):
    while True:
        texto = ler_entrada(mensagem).strip()
        try:
            valor = int(texto)
        except ValueError:
            print("  [!] Digite apenas um número inteiro.")
            continue
        if minimo is not None and valor < minimo:
            print(f"  [!] O número deve ser maior ou igual a {minimo}.")
            continue
        if maximo is not None and valor > maximo:
            print(f"  [!] O número deve ser menor ou igual a {maximo}.")
            continue
        return valor


def ler_decimal(mensagem, minimo=None, maximo=None, permitir_vazio=False):
    while True:
        texto = ler_entrada(mensagem).strip()
        if permitir_vazio and not texto:
            return None
        try:
            valor = float(texto.replace(",", "."))
        except ValueError:
            print("  [!] Valor inválido. Digite um número (ex.: 35 ou 35,50).")
            continue
        if not math.isfinite(valor):
            print("  [!] Valor inválido. Digite um número finito.")
            continue
        if minimo is not None and valor < minimo:
            print(f"  [!] O valor deve ser maior ou igual a {minimo}.")
            continue
        if maximo is not None and valor > maximo:
            print(f"  [!] O valor deve ser menor ou igual a {maximo}.")
            continue
        return valor


def escolher(lista, rotulo="item"):
    if not lista:
        print(f"  [!] Nenhum(a) {rotulo} cadastrado(a).")
        return None
    for i, item in enumerate(lista, 1):
        print(f"  [{i}] {item.nome}")
    while True:
        indice = ler_inteiro(
            f"  Escolha o número do(a) {rotulo} (0 para cancelar): ",
            0,
            len(lista),
        )
        if indice == 0:
            print("  Operação cancelada.")
            return None
        return lista[indice - 1]


def escolher_produto(empresa):
    if not empresa.produtos:
        print("  [!] Esta marisqueira não possui produtos cadastrados.")
        return None
    for i, p in enumerate(empresa.produtos, 1):
        disp = "Disponível" if p.quantidade > 0 else "Indisponível"
        print(f"  [{i}] {p.nome} | {p.categoria} | R${p.preco:.2f}/kg | {p.quantidade}kg [{disp}]")
    while True:
        indice = ler_inteiro(
            "  Escolha o número do produto (0 para cancelar): ",
            0,
            len(empresa.produtos),
        )
        if indice == 0:
            print("  Operação cancelada.")
            return None
        return empresa.produtos[indice - 1]


# == SUBMENU: MARISQUEIRAS ==
def menu_marisqueiras():
    while True:
        titulo("MENU — Empresas Marisqueiras")
        print("  [1] Criar nova marisqueira")
        print("  [2] Listar marisqueiras")
        print("  [3] Cadastrar produto em marisqueira")
        print("  [4] Alterar quantidade de produto")
        print("  [5] Ver status visual (Semáforo)")
        print("  [6] Ver avaliações")
        print("  [0] Voltar")
        linha()
        op = ler_opcao("  Opção: ", ["1", "2", "3", "4", "5", "6", "0"])

        if op == "1":
            nome = ler_nome("  Nome da marisqueira: ")
            if any(m.nome.lower() == nome.lower() for m in marisqueiras_cadastradas):
                print(f"  [!] Já existe uma marisqueira chamada '{nome}'.")
                continue
            loc = ler_texto("  Localização: ")
            m = EmpresaMarisqueira(nome, loc)
            marisqueiras_cadastradas.append(m)
            print(f"  [✓] '{nome}' criada com sucesso!")

        elif op == "2":
            titulo("Marisqueiras Cadastradas")
            if not marisqueiras_cadastradas:
                print("  Nenhuma marisqueira cadastrada.")
            for m in marisqueiras_cadastradas:
                media = m.media_avaliacoes()
                aval  = f"{media:.1f} estrelas" if m.avaliacoes else "Sem avaliação"
                print(f"  • {m.nome} | {m.localizacao} | {len(m.produtos)} produto(s) | {aval}")

        elif op == "3":
            linha()
            print("  Escolha a marisqueira:")
            m = escolher(marisqueiras_cadastradas, "marisqueira")
            if m is None:
                continue
            nome = ler_nome("  Nome do produto: ")
            print("  Categorias aceitas: fresco / congelado")
            cat = ler_opcao("  Categoria: ", ["fresco", "congelado"])
            preco = ler_decimal("  Preço (R$/kg): ", minimo=0.01)
            qtd = ler_decimal("  Quantidade (kg, mín. 25kg): ", minimo=25)
            p = Produto(nome, cat, preco, qtd)
            m.cadastrar_produto(p)

        elif op == "4":
            linha()
            print("  Escolha a marisqueira:")
            m = escolher(marisqueiras_cadastradas, "marisqueira")
            if m is None:
                continue
            p = escolher_produto(m)
            if p is None:
                continue
            nova = ler_decimal(f"  Nova quantidade para '{p.nome}' (kg): ", minimo=0)
            m.alterar_quantidade(p, nova)

        elif op == "5":
            linha()
            print("  Escolha a marisqueira:")
            m = escolher(marisqueiras_cadastradas, "marisqueira")
            if m is None:
                continue
            em_hora = ler_opcao("  Está em horário de funcionamento? (s/n): ", ["s", "n"])
            status = m.obter_status_visual(em_hora == "s")
            print(f"  Status visual: {status}")

        elif op == "6":
            linha()
            print("  Escolha a marisqueira:")
            m = escolher(marisqueiras_cadastradas, "marisqueira")
            if m is None:
                continue
            if not m.avaliacoes:
                print("  Sem avaliações registradas.")
            else:
                for a in m.avaliacoes:
                    print(f"  • {a.empresa_compradora.nome}: {a.nota} estrela(s)")
                print(f"  Média: {m.media_avaliacoes():.1f} estrelas")

        elif op == "0":
            break
        else:
            print("  [!] Opção inválida.")


# == SUBMENU: COMPRADORAS ==
def menu_compradoras():
    while True:
        titulo("MENU — Empresas Compradoras")
        print("  [1] Criar nova compradora")
        print("  [2] Listar compradoras")
        print("  [3] Consultar / Filtrar produtos")
        print("  [4] Comparar dois produtos")
        print("  [5] Avaliar marisqueira")
        print("  [0] Voltar")
        linha()
        op = ler_opcao("  Opção: ", ["1", "2", "3", "4", "5", "0"])

        if op == "1":
            nome = ler_nome("  Nome da compradora: ")
            if any(c.nome.lower() == nome.lower() for c in compradoras_cadastradas):
                print(f"  [!] Já existe uma compradora chamada '{nome}'.")
                continue
            loc = ler_texto("  Localização: ")
            c = EmpresaCompradora(nome, loc)
            compradoras_cadastradas.append(c)
            print(f"  [✓] '{nome}' criada com sucesso!")

        elif op == "2":
            titulo("Compradoras Cadastradas")
            if not compradoras_cadastradas:
                print("  Nenhuma compradora cadastrada.")
            for c in compradoras_cadastradas:
                print(f"  • {c.nome} | {c.localizacao}")

        elif op == "3":
            linha()
            todos = []
            for m in marisqueiras_cadastradas:
                todos.extend(m.produtos)
            if not todos:
                print("  [!] Nenhum produto cadastrado em nenhuma marisqueira.")
                continue

            print("  Filtros (pressione Enter para ignorar):")
            f_nome = ler_texto_opcional("  Nome do produto: ")
            f_cat = ler_opcao(
                "  Categoria (fresco/congelado): ",
                ["fresco", "congelado"],
                permitir_vazio=True,
            )
            f_loc = ler_texto_opcional("  Localização da marisqueira: ")
            f_emp = ler_texto_opcional("  Nome da marisqueira: ")
            f_aval = ler_decimal(
                "  Avaliação mínima (1 a 5, ou Enter): ",
                minimo=1,
                maximo=5,
                permitir_vazio=True,
            )
            print("  Opções de ordenação: menor_preco | maior_preco | melhor_avaliacao | localizacao | (Enter=nenhuma)")
            ordem = ler_opcao(
                "  Ordenar por: ",
                ["menor_preco", "maior_preco", "melhor_avaliacao", "localizacao"],
                permitir_vazio=True,
            )

            c = compradoras_cadastradas[0] if compradoras_cadastradas else EmpresaCompradora("Consulta", "N/A")
            resultados = c.consultar_produtos(
                todos,
                filtro_nome=f_nome,
                filtro_categoria=f_cat,
                filtro_localizacao=f_loc,
                filtro_empresa=f_emp,
                filtro_avaliacao=f_aval,
                ordenar_por=ordem
            )
            linha()
            if not resultados:
                print("  Nenhum produto encontrado com esses filtros.")
            else:
                print(f"  {len(resultados)} produto(s) encontrado(s):")
                for r in resultados:
                    disp = "disponível" if r.quantidade > 0 else "indisponível"
                    aval = f"{r.empresa.media_avaliacoes():.1f}★" if r.empresa.avaliacoes else "sem avaliação"
                    print(f"  • {r.nome} | {r.categoria} | R${r.preco:.2f}/kg"
                          f" | {r.quantidade}kg | {r.empresa.nome} [{aval}] | ({disp})")

        elif op == "4":
            linha()
            todos = []
            for m in marisqueiras_cadastradas:
                todos.extend(m.produtos)
            if len(todos) < 2:
                print("  [!] São necessários pelo menos 2 produtos cadastrados.")
                continue
            for i, p in enumerate(todos, 1):
                print(f"  [{i}] {p.nome} ({p.empresa.nome})")
            while True:
                idx1 = ler_inteiro(
                    f"  Número do produto 1 (1-{len(todos)}): ",
                    1,
                    len(todos),
                )
                idx2 = ler_inteiro(
                    f"  Número do produto 2 (1-{len(todos)}): ",
                    1,
                    len(todos),
                )
                if idx1 == idx2:
                    print("  [!] Escolha dois produtos diferentes.")
                    continue
                break
            c = compradoras_cadastradas[0] if compradoras_cadastradas else EmpresaCompradora("Consulta", "N/A")
            print()
            print(c.comparar_produtos(todos[idx1 - 1], todos[idx2 - 1]))

        elif op == "5":
            linha()
            print("  Escolha a compradora que vai avaliar:")
            c = escolher(compradoras_cadastradas, "compradora")
            if c is None:
                continue
            print("  Escolha a marisqueira a ser avaliada:")
            m = escolher(marisqueiras_cadastradas, "marisqueira")
            if m is None:
                continue
            nota = ler_inteiro("  Nota (1 a 5): ", 1, 5)
            c.avaliar_empresa(m, nota)

        elif op == "0":
            break
        else:
            print("  [!] Opção inválida.")


# == SUBMENU: PEDIDOS ==
def menu_pedidos():
    while True:
        titulo("MENU — Pedidos")
        print("  [1] Criar novo pedido")
        print("  [2] Adicionar item a pedido pendente")
        print("  [3] Listar todos os pedidos")
        print("  [4] Ver detalhes de um pedido")
        print("  [5] Marisqueira: receber pedido")
        print("  [6] Marisqueira: aceitar pedido (desconta estoque)")
        print("  [7] Marisqueira: rejeitar pedido")
        print("  [8] Marisqueira: solicitar ajuste")
        print("  [9] Marisqueira: atualizar status de entrega")
        print("  [0] Voltar")
        linha()
        op = ler_opcao("  Opção: ", ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0"])

        if op == "1":
            linha()
            print("  Escolha a compradora:")
            c = escolher(compradoras_cadastradas, "compradora")
            if c is None:
                continue
            end = ler_texto("  Endereço de entrega: ")
            tempo = ler_texto("  Tempo de entrega estimado: ")
            p = c.realizar_pedido(end, tempo)
            if p:
                pedidos_cadastrados.append(p)
                print(f"  [✓] Pedido #{len(pedidos_cadastrados)} criado com sucesso!")

        elif op == "2":
            linha()
            pendentes = [p for p in pedidos_cadastrados if p.status in ("Pendente", "Ajuste Solicitado")]
            if not pendentes:
                print("  [!] Nenhum pedido em status 'Pendente' ou 'Ajuste Solicitado'.")
                continue
            print("  Pedidos disponíveis para edição:")
            for i, p in enumerate(pendentes, 1):
                print(f"  [{i}] Pedido #{pedidos_cadastrados.index(p)+1} — {p.empresa_compradora.nome}"
                      f" | Status: {p.status} | Itens atuais: {len(p.itens)}")
            idx = ler_inteiro(f"  Escolha o pedido (1-{len(pendentes)}): ", 1, len(pendentes))
            pedido = pendentes[idx - 1]

            print("  Escolha a marisqueira do produto:")
            m = escolher(marisqueiras_cadastradas, "marisqueira")
            if m is None:
                continue
            print("  Escolha o produto:")
            prod = escolher_produto(m)
            if prod is None:
                continue
            qtd = ler_decimal("  Quantidade (kg, mínimo 25kg): ", minimo=25)
            pedido.adicionar_item(prod, qtd)

        elif op == "3":
            titulo("Lista de Pedidos")
            if not pedidos_cadastrados:
                print("  Nenhum pedido criado até o momento.")
            for i, p in enumerate(pedidos_cadastrados, 1):
                mar = p.empresa_marisqueira.nome if p.empresa_marisqueira else "Sem marisqueira definida"
                print(f"  Pedido #{i} | {p.empresa_compradora.nome} → {mar}"
                      f" | Status: {p.status} | Entrega: {p.status_entrega}"
                      f" | Itens: {len(p.itens)}")

        elif op == "4":
            linha()
            if not pedidos_cadastrados:
                print("  [!] Nenhum pedido cadastrado.")
                continue
            for i, p in enumerate(pedidos_cadastrados, 1):
                print(f"  [{i}] Pedido #{i} — {p.empresa_compradora.nome} | {p.status}")
            idx = ler_inteiro(
                f"  Número do pedido (1-{len(pedidos_cadastrados)}): ",
                1,
                len(pedidos_cadastrados),
            )
            p = pedidos_cadastrados[idx - 1]
            linha()
            print(f"  Detalhes do Pedido #{idx}")
            print(f"  Compradora    : {p.empresa_compradora.nome}")
            print(f"  Marisqueira   : {p.empresa_marisqueira.nome if p.empresa_marisqueira else 'Nenhuma'}")
            print(f"  Endereço      : {p.endereco_entrega}")
            print(f"  Tempo entrega : {p.tempo_entrega}")
            print(f"  Status        : {p.status}")
            print(f"  Status entrega: {p.status_entrega}")
            total = 0.0
            print("  Itens:")
            for it in p.itens:
                subtotal = it.quantidade * it.preco_unitario
                total += subtotal
                print(f"    • {it.produto.nome} | {it.quantidade}kg × R${it.preco_unitario:.2f} = R${subtotal:.2f}")
            print(f"  VALOR TOTAL: R${total:.2f}")

        elif op == "5":
            linha()
            print("  Escolha a marisqueira:")
            m = escolher(marisqueiras_cadastradas, "marisqueira")
            if m is None:
                continue
            pendentes = [p for p in pedidos_cadastrados if p.status == "Pendente" and p.empresa_marisqueira == m]
            if not pendentes:
                print("  [!] Sem pedidos 'Pendente' para esta marisqueira.")
                continue
            for i, p in enumerate(pendentes, 1):
                print(f"  [{i}] Pedido #{pedidos_cadastrados.index(p)+1} — {p.empresa_compradora.nome}")
            idx = ler_inteiro(f"  Escolha (1-{len(pendentes)}): ", 1, len(pendentes))
            m.receber_pedido(pendentes[idx - 1])

        elif op == "6":
            linha()
            print("  Escolha a marisqueira:")
            m = escolher(marisqueiras_cadastradas, "marisqueira")
            if m is None:
                continue
            disponiveis = [p for p in pedidos_cadastrados if p.status in ("Recebido", "Ajuste Solicitado") and p.empresa_marisqueira == m]
            if not disponiveis:
                print("  [!] Sem pedidos 'Recebido' ou 'Ajuste Solicitado' para esta marisqueira.")
                continue
            for i, p in enumerate(disponiveis, 1):
                print(f"  [{i}] Pedido #{pedidos_cadastrados.index(p)+1} — {p.empresa_compradora.nome} | Status: {p.status}")
            idx = ler_inteiro(f"  Escolha (1-{len(disponiveis)}): ", 1, len(disponiveis))
            m.aceitar_pedido(disponiveis[idx - 1])

        elif op == "7":
            linha()
            print("  Escolha a marisqueira:")
            m = escolher(marisqueiras_cadastradas, "marisqueira")
            if m is None:
                continue
            rejeitaveis = [p for p in pedidos_cadastrados if p.status not in ("Aceito", "Rejeitado") and p.empresa_marisqueira == m]
            if not rejeitaveis:
                print("  [!] Sem pedidos rejeitáveis para esta marisqueira.")
                continue
            for i, p in enumerate(rejeitaveis, 1):
                print(f"  [{i}] Pedido #{pedidos_cadastrados.index(p)+1} — {p.empresa_compradora.nome} | Status: {p.status}")
            idx = ler_inteiro(f"  Escolha (1-{len(rejeitaveis)}): ", 1, len(rejeitaveis))
            m.rejeitar_pedido(rejeitaveis[idx - 1])

        elif op == "8":
            linha()
            print("  Escolha a marisqueira:")
            m = escolher(marisqueiras_cadastradas, "marisqueira")
            if m is None:
                continue
            ajustaveis = [p for p in pedidos_cadastrados if p.status == "Recebido" and p.empresa_marisqueira == m]
            if not ajustaveis:
                print("  [!] Sem pedidos 'Recebido' para solicitar ajuste.")
                continue
            for i, p in enumerate(ajustaveis, 1):
                print(f"  [{i}] Pedido #{pedidos_cadastrados.index(p)+1} — {p.empresa_compradora.nome}")
            idx = ler_inteiro(f"  Escolha (1-{len(ajustaveis)}): ", 1, len(ajustaveis))
            m.solicitar_ajuste(ajustaveis[idx - 1])

        elif op == "9":
            linha()
            print("  Escolha a marisqueira:")
            m = escolher(marisqueiras_cadastradas, "marisqueira")
            if m is None:
                continue
            aceitos = [p for p in pedidos_cadastrados if p.status == "Aceito" and p.empresa_marisqueira == m]
            if not aceitos:
                print("  [!] Sem pedidos aceitos para atualizar entrega.")
                continue
            for i, p in enumerate(aceitos, 1):
                print(f"  [{i}] Pedido #{pedidos_cadastrados.index(p)+1} — {p.empresa_compradora.nome} | Entrega atual: {p.status_entrega}")
            idx = ler_inteiro(f"  Escolha (1-{len(aceitos)}): ", 1, len(aceitos))
            print("  Opções: [1] Em preparação | [2] Em trânsito | [3] Entregue")
            novo_status = ler_opcao(
                "  Novo status de entrega: ",
                {"1": "Em preparação", "2": "Em trânsito", "3": "Entregue"},
            )
            m.atualizar_status_entrega(aceitos[idx - 1], novo_status)

        elif op == "0":
            break
        else:
            print("  [!] Opção inválida.")


# == CARREGAR DADOS DE EXEMPLO ==
def carregar_dados_demo():
    global dados_demo_carregados
    if dados_demo_carregados:
        print("  [!] Os dados de demonstração já foram carregados.")
        return

    m1 = EmpresaMarisqueira("Mariscos da Ilha", "Ilha de Deus")
    m2 = EmpresaMarisqueira("Frutos do Mar LTDA", "Brasília Teimosa")
    marisqueiras_cadastradas.extend([m1, m2])

    p1 = Produto("Sururu", "fresco", 35.0, 100)
    p2 = Produto("Marisco", "congelado", 25.0, 40)
    p3 = Produto("Ostra", "fresco", 50.0, 80)
    m1.cadastrar_produto(p1)
    m1.cadastrar_produto(p2)
    m2.cadastrar_produto(p3)

    c1 = EmpresaCompradora("Restaurante Sabor do Mar", "Boa Viagem")
    c2 = EmpresaCompradora("Cantina do Porto", "Recife Antigo")
    compradoras_cadastradas.extend([c1, c2])
    dados_demo_carregados = True

    print("\n  [✓] Dados de demonstração carregados com sucesso!")
    print("  • 2 Marisqueiras: 'Mariscos da Ilha' e 'Frutos do Mar LTDA'")
    print("  • 3 Produtos: Sururu (100kg), Marisco (40kg), Ostra (80kg)")
    print("  • 2 Compradoras: 'Restaurante Sabor do Mar' e 'Cantina do Porto'")


# == MENU PRINCIPAL ==
def main():
    while True:
        titulo("SISTEMA DE MARISQUEIRAS — Menu Principal")
        print("  [1] Gerenciar Empresas Marisqueiras")
        print("  [2] Gerenciar Empresas Compradoras")
        print("  [3] Gerenciar Pedidos")
        print("  [D] Carregar dados de demonstração (pré-cadastrados)")
        print("  [0] Sair")
        linha()
        op = ler_opcao("  Escolha uma opção: ", ["1", "2", "3", "D", "0"])

        if op == "1":
            menu_marisqueiras()
        elif op == "2":
            menu_compradoras()
        elif op == "3":
            menu_pedidos()
        elif op == "D":
            carregar_dados_demo()
        elif op == "0":
            print("\n  Encerrando o programa. Até logo!\n")
            break


if __name__ == "__main__":
    try:
        main()
    except (EntradaEncerrada, KeyboardInterrupt):
        print("\n\n  Encerrando o programa. Até logo!\n")

