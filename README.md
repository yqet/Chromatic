# Chromatic

**Chromatic** é uma ferramenta leve para edição e recoloração de texturas de Minecraft, criada por **blinkzin**.

O projeto foi desenvolvido para facilitar a edição de Resource Packs, permitindo selecionar elementos específicos, alterar suas cores e visualizar o resultado em um preview 3D antes de exportar a textura.

> **Status:** versão 1.0 — foco em Minecraft 1.5.2 e 1.8.x

## ✨ Recursos

- 🎨 Recoloração de texturas por item/elemento
- 🔍 Detecção automática da versão do Resource Pack
- 📦 Suporte a Resource Packs em pasta, `.zip`, `.rar` e `.7z`
- 🧩 Adapters separados para Minecraft 1.5.2 e 1.8.x
- 🖼️ Preservação das dimensões e estrutura das texturas
- 🧍 Preview 3D das alterações
- 🎮 Visualização de armaduras, espadas e outros itens
- 🌙 Interface com modo escuro e claro
- 🇧🇷 Interface preparada para uso em português e inglês

## 🕹️ Versões suportadas

| Minecraft | Suporte |
|---|---|
| **1.5.2** | ✅ |
| **1.8.x** | ✅ |

A versão é identificada automaticamente a partir da estrutura/metadados do Resource Pack quando disponíveis. O usuário não precisa selecionar manualmente a versão no programa.

## 📦 Formatos de entrada

O Chromatic consegue trabalhar com:

- Pasta de Resource Pack
- `.zip`
- `.rar`
- `.7z`

O projeto adapta a leitura de acordo com a versão detectada e utiliza adapters específicos para manter as diferenças entre versões isoladas.

## 🏗️ Estrutura do projeto

```text
Chromatic/
├── recolor_gui.py          # Interface gráfica principal
├── recolor_engine.py       # Engine de leitura, análise e recoloração
├── preview_dialog.py       # Preview 3D / Inspect Edits
├── adapters/
│   ├── __init__.py
│   ├── mc_152.py           # Adapter Minecraft 1.5.2
│   ├── mc_189.py           # Adapter Minecraft 1.8.x
│   ├── 1.5.2.json          # Mapeamentos da 1.5.2
│   └── 1.6.1-1.8.9.json    # Mapeamentos da família 1.8.x
├── Abrir_Chromatic.bat     # Inicializador para desenvolvimento
├── requirements.txt        # Dependências Python
├── .gitignore
└── README.md
```

## 🧠 Arquitetura

O Chromatic separa a aplicação em três partes principais:

### GUI

`recolor_gui.py` controla a interface, seleção dos elementos, configurações de cor e interação do usuário.

### Engine

`recolor_engine.py` é responsável pelo processamento das texturas e pelas operações de recoloração.

### Adapters

Cada versão do Minecraft possui diferenças na organização dos assets e nos nomes dos itens. Os adapters isolam essas diferenças para que a engine principal não precise conhecer detalhes específicos de cada versão.

```text
Resource Pack
      │
      ▼
Version Detection
      │
      ├── Minecraft 1.5.2 ──► mc_152
      │
      └── Minecraft 1.8.x ──► mc_189
      │
      ▼
   Recolor Engine
      │
      ▼
  Edited Texture
      │
      ▼
   3D Preview
```

## 🛠️ Desenvolvimento

Requisitos:

- Windows
- Python 3.x
- Dependências listadas em `requirements.txt`

Instalação:

```bash
pip install -r requirements.txt
```

Execução:

```bash
python recolor_gui.py
```

Ou, no Windows:

```text
Abrir_Chromatic.bat
```

## 👤 Autor

**blinkzin**

Chromatic foi criado e desenvolvido por blinkzin.

## 📄 Licença

A licença do projeto será definida pelo autor antes da publicação final no GitHub.
