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
        if self.quantidade <= 0:
            return False
        return self.quantidade >= quantidade_solicitada

    def atualizar_quantidade(self, nova_quantidade):
        # Quantidade não pode ficar negativa; produto fica indisponível ao chegar a zero
        self.quantidade = max(0, nova_quantidade)


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
        return quantidade >= 25

    def verificar_disponibilidade(self, produto, quantidade):
        return produto.verificar_disponibilidade(quantidade)


class Avaliacao:
    def __init__(self, empresa_compradora):
        self.empresa_compradora = empresa_compradora
        self.nota = 0

    def registrar_nota(self, nota):
        if not isinstance(nota, int):
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
        if not produto.nome or not produto.nome.strip():
            print("Erro: Nome do produto não pode ser vazio.")
            return False
        if produto.categoria not in ("fresco", "congelado"):
            print(f"Erro: Categoria '{produto.categoria}' inválida. Use 'fresco' ou 'congelado'.")
            return False
        if not isinstance(produto.preco, (int, float)):
            print("Erro: Preço deve ser um número.")
            return False
        if not isinstance(produto.quantidade, (int, float)):
            print("Erro: Quantidade deve ser um número.")
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
        if produto not in self.produtos:
            print(f"Erro: Produto '{produto.nome}' não pertence a esta empresa.")
            return
        if nova_quantidade < 0:
            print("Erro: Quantidade não pode ser negativa. Nenhuma alteração feita.")
            return
        produto.atualizar_quantidade(nova_quantidade)
        print(f"[{self.nome}] Quantidade de '{produto.nome}' atualizada para {produto.quantidade}kg.")

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
        pedido.status_entrega = status
        print(f"[{self.nome}] Status da entrega atualizado para: '{status}'.")
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
            if filtro_nome and filtro_nome.lower() not in p.nome.lower():
                continue
            if filtro_categoria and filtro_categoria.lower() != p.categoria.lower():
                continue
            if filtro_localizacao and filtro_localizacao.lower() not in p.empresa.localizacao.lower():
                continue
            if filtro_empresa and filtro_empresa.lower() not in p.empresa.nome.lower():
                continue
            if filtro_avaliacao and p.empresa.media_avaliacoes() < filtro_avaliacao:
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
        if not endereco_entrega or not endereco_entrega.strip():
            print("Erro: Endereço de entrega não pode ser vazio.")
            return None
        if not tempo_entrega or not tempo_entrega.strip():
            print("Erro: Tempo de entrega não pode ser vazio.")
            return None
        return Pedido(self, endereco_entrega, tempo_entrega)

    def avaliar_empresa(self, empresa_marisqueira, nota):
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


def linha():
    print("─" * 55)


def titulo(texto):
    print(f"\n{'=' * 55}")
    print(f"  {texto}")
    print(f"{'=' * 55}")


def escolher(lista, rotulo="item"):
    if not lista:
        print(f"  [!] Nenhum(a) {rotulo} cadastrado(a).")
        return None
    for i, item in enumerate(lista, 1):
        print(f"  [{i}] {item.nome}")
    try:
        idx = int(input(f"  Escolha o número do(a) {rotulo}: ")) - 1
        if 0 <= idx < len(lista):
            return lista[idx]
    except ValueError:
        pass
    print("  [!] Opção inválida.")
    return None


def escolher_produto(empresa):
    if not empresa.produtos:
        print("  [!] Esta marisqueira não possui produtos cadastrados.")
        return None
    for i, p in enumerate(empresa.produtos, 1):
        disp = "Disponível" if p.quantidade > 0 else "Indisponível"
        print(f"  [{i}] {p.nome} | {p.categoria} | R${p.preco:.2f}/kg | {p.quantidade}kg [{disp}]")
    try:
        idx = int(input("  Escolha o número do produto: ")) - 1
        if 0 <= idx < len(empresa.produtos):
            return empresa.produtos[idx]
    except ValueError:
        pass
    print("  [!] Opção inválida.")
    return None


def pedir_float(msg):
    try:
        return float(input(msg))
    except ValueError:
        print("  [!] Valor inválido.")
        return None


def pedir_int(msg):
    try:
        return int(input(msg))
    except ValueError:
        print("  [!] Valor inválido.")
        return None


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
        op = input("  Opção: ").strip()

        if op == "1":
            nome = input("  Nome da marisqueira: ").strip()
            loc  = input("  Localização: ").strip()
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
            nome = input("  Nome do produto: ").strip()
            print("  Categorias aceitas: fresco / congelado")
            cat  = input("  Categoria: ").strip()
            preco = pedir_float("  Preço (R$/kg): ")
            if preco is None:
                continue
            qtd = pedir_float("  Quantidade (kg, mín. 25kg): ")
            if qtd is None:
                continue
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
            nova = pedir_float(f"  Nova quantidade para '{p.nome}' (kg): ")
            if nova is None:
                continue
            m.alterar_quantidade(p, nova)

        elif op == "5":
            linha()
            print("  Escolha a marisqueira:")
            m = escolher(marisqueiras_cadastradas, "marisqueira")
            if m is None:
                continue
            em_hora = input("  Está em horário de funcionamento? (s/n): ").strip().lower()
            status = m.obter_status_visual(em_hora != "n")
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
        op = input("  Opção: ").strip()

        if op == "1":
            nome = input("  Nome da compradora: ").strip()
            loc  = input("  Localização: ").strip()
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
            f_nome = input("  Nome do produto: ").strip() or None
            f_cat  = input("  Categoria (fresco/congelado): ").strip() or None
            f_loc  = input("  Localização da marisqueira: ").strip() or None
            f_emp  = input("  Nome da marisqueira: ").strip() or None
            f_aval_str = input("  Avaliação mínima (1 a 5, ou Enter): ").strip()
            f_aval = float(f_aval_str) if f_aval_str else None
            print("  Opções de ordenação: menor_preco | maior_preco | melhor_avaliacao | localizacao | (Enter=nenhuma)")
            ordem = input("  Ordenar por: ").strip() or None

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
            idx1 = pedir_int("  Número do produto 1: ")
            idx2 = pedir_int("  Número do produto 2: ")
            if idx1 is None or idx2 is None:
                continue
            if not (1 <= idx1 <= len(todos) and 1 <= idx2 <= len(todos)):
                print("  [!] Índices inválidos.")
                continue
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
            nota = pedir_int("  Nota (1 a 5): ")
            if nota is None:
                continue
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
        op = input("  Opção: ").strip()

        if op == "1":
            linha()
            print("  Escolha a compradora:")
            c = escolher(compradoras_cadastradas, "compradora")
            if c is None:
                continue
            end   = input("  Endereço de entrega: ").strip()
            tempo = input("  Tempo de entrega estimado: ").strip()
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
            try:
                idx = int(input("  Escolha o pedido: ")) - 1
                if not (0 <= idx < len(pendentes)):
                    print("  [!] Opção inválida.")
                    continue
            except ValueError:
                print("  [!] Valor inválido.")
                continue
            pedido = pendentes[idx]

            print("  Escolha a marisqueira do produto:")
            m = escolher(marisqueiras_cadastradas, "marisqueira")
            if m is None:
                continue
            print("  Escolha o produto:")
            prod = escolher_produto(m)
            if prod is None:
                continue
            qtd = pedir_float("  Quantidade (kg, mínimo 25kg): ")
            if qtd is None:
                continue
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
            idx = pedir_int("  Número do pedido: ")
            if idx is None or not (1 <= idx <= len(pedidos_cadastrados)):
                continue
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
            idx = pedir_int("  Escolha: ")
            if idx is None or not (1 <= idx <= len(pendentes)):
                continue
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
            idx = pedir_int("  Escolha: ")
            if idx is None or not (1 <= idx <= len(disponiveis)):
                continue
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
            idx = pedir_int("  Escolha: ")
            if idx is None or not (1 <= idx <= len(rejeitaveis)):
                continue
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
            idx = pedir_int("  Escolha: ")
            if idx is None or not (1 <= idx <= len(ajustaveis)):
                continue
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
            idx = pedir_int("  Escolha: ")
            if idx is None or not (1 <= idx <= len(aceitos)):
                continue
            print("  Opções: Em preparação | Em trânsito | Entregue")
            novo_status = input("  Novo status de entrega: ").strip()
            m.atualizar_status_entrega(aceitos[idx - 1], novo_status)

        elif op == "0":
            break
        else:
            print("  [!] Opção inválida.")


# == CARREGAR DADOS DE EXEMPLO ==
def carregar_dados_demo():
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
        op = input("  Escolha uma opção: ").strip().upper()

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
        else:
            print("  [!] Opção inválida. Tente novamente.")


if __name__ == "__main__":
    main()

