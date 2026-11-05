import streamlit as st
from datetime import date

from database import (
    add_batch,
    add_product,
    add_promotion,
    get_alert_level,
    get_batches_for_dashboard,
    get_loss_report,
    get_products,
    get_products_for_alerts,
    get_promotions,
    get_status_report,
    init_db,
    update_batch_status,
    update_product_status,
    validate_nf_key,
)


init_db()

st.set_page_config(page_title="Rastreador de Validade", layout="wide")

st.markdown(
    """
    <style>
        html, body, [data-testid="stAppViewContainer"] {
            background: linear-gradient(180deg, #0b0713 0%, #140d22 100%);
            color: #f5f3ff;
        }
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #1a102d 0%, #120b1f 100%);
            border-right: 1px solid rgba(166, 122, 255, 0.35);
        }
        .stApp {
            color: #f5f3ff;
        }
        h1, h2, h3, h4, h5, h6, p, label, div, span {
            color: #f5f3ff;
        }
        .stTextInput > div > div > input,
        .stNumberInput > div > div > input,
        .stDateInput input,
        .stSelectbox > div > div,
        .stDataFrame {
            background: #1a1325;
            color: #f5f3ff;
            border: 1px solid rgba(166, 122, 255, 0.5);
            border-radius: 8px;
        }
        .stButton > button {
            background: linear-gradient(135deg, #8a5cf6 0%, #6d3de0 100%);
            color: #ffffff;
            border: none;
            border-radius: 10px;
            padding: 0.55rem 1.25rem;
            font-weight: 600;
            box-shadow: 0 6px 18px rgba(138, 92, 246, 0.35);
        }
        .stButton > button:hover {
            background: linear-gradient(135deg, #9b6dff 0%, #7a45f4 100%);
            color: #ffffff;
        }
        .stSuccess {
            background-color: rgba(34, 197, 94, 0.12);
            color: #dcfce7;
            border: 1px solid rgba(34, 197, 94, 0.45);
        }
        .stError {
            background-color: rgba(239, 68, 68, 0.12);
            color: #fecaca;
            border: 1px solid rgba(239, 68, 68, 0.45);
        }
        .stWarning {
            background-color: rgba(245, 158, 11, 0.12);
            color: #fef3c7;
            border: 1px solid rgba(245, 158, 11, 0.45);
        }
        .stInfo {
            background-color: rgba(59, 130, 246, 0.12);
            color: #dbeafe;
            border: 1px solid rgba(59, 130, 246, 0.45);
        }
        .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("Rastreador de Validade")

st.sidebar.title("Menu")
page = st.sidebar.radio("Navegação", ["Produtos", "Entrada de lotes", "Alertas", "Promoção", "Relatório de perdas"])

if page == "Produtos":
    st.subheader("Cadastrar produto")
    with st.form("product_form"):
        barcode = st.text_input("Código de barras")
        description = st.text_input("Descrição")
        category = st.text_input("Categoria")
        cost_price = st.number_input("Preço de custo", min_value=0.0, step=0.01)
        expiry_date = st.date_input("Data de validade")
        submitted = st.form_submit_button("Salvar produto")
        if submitted:
            if not barcode or not description or not category:
                st.warning("Preencha todos os campos.")
            elif add_product(barcode, description, category, float(cost_price), expiry_date.isoformat()):
                st.success("Produto cadastrado com sucesso.")
            else:
                st.error("Esse código de barras já existe.")

    st.subheader("Produtos cadastrados")
    products = get_products()
    if products:
        translated_products = [
            {
                "ID": item["id"],
                "Código de barras": item["barcode"],
                "Descrição": item["description"],
                "Categoria": item["category"],
                "Preço de custo": item["cost_price"],
                "Data de validade": item["expiry_date"],
            }
            for item in products
        ]
        st.dataframe(translated_products, use_container_width=True)
    else:
        st.info("Ainda não há produtos cadastrados.")

elif page == "Entrada de lotes":
    st.subheader("Entrada de lote via nota fiscal")
    with st.form("batch_form"):
        invoice_key = st.text_input("Chave de acesso da NF-e (44 dígitos)")
        supplier = st.text_input("Fornecedor")
        entry_date = st.date_input("Data de entrada")
        barcode = st.text_input("Código de barras do produto")
        quantity = st.number_input("Quantidade", min_value=1, step=1)
        batch_number = st.text_input("Lote")
        expiry_date = st.date_input("Data de validade")
        submitted = st.form_submit_button("Cadastrar lote")
        if submitted:
            if not validate_nf_key(invoice_key):
                st.error("A chave da NF-e deve conter exatamente 44 dígitos numéricos.")
            else:
                try:
                    add_batch(
                        invoice_key=invoice_key,
                        supplier=supplier,
                        entry_date=entry_date.isoformat(),
                        barcode=barcode,
                        quantity=int(quantity),
                        batch_number=batch_number,
                        expiry_date=expiry_date.isoformat(),
                    )
                    st.success("Lote cadastrado com sucesso.")
                except ValueError as exc:
                    st.error(str(exc))

elif page == "Alertas":
    st.subheader("Painel de alertas")
    batches = get_batches_for_dashboard()
    products_for_alerts = get_products_for_alerts()
    status_labels = {
        "available": "Disponível",
        "sold": "Vendido",
        "promoted": "Em promoção",
        "returned": "Devolvido",
        "discarded": "Descartado",
    }
    level_labels = {
        "expired": "Vencido",
        "critical": "Crítico",
        "warning": "Atenção",
        "attention": "Próximo",
        "healthy": "Saudável",
    }

    if not batches and not products_for_alerts:
        st.info("Nenhum lote ou produto em alerta.")
    else:
        for product in products_for_alerts:
            expiry = date.fromisoformat(product["expiry_date"])
            level = get_alert_level(expiry)
            color = {
                "expired": "#ff4d4d",
                "critical": "#ffb84d",
                "warning": "#ffd966",
                "attention": "#7ad9ff",
                "healthy": "#7fe98f",
            }.get(level, "#d9d9d9")
            st.markdown(
                f"<div style='background-color:{color}; color:#111827; padding:12px; border-radius:8px; margin-bottom:10px;'>"
                f"<strong>{product['description']}</strong> | Código: {product['barcode']} | Categoria: {product['category']} | Validade: {product['expiry_date']} | Nível: {level_labels.get(level, level)}</div>",
                unsafe_allow_html=True,
            )
            action_col1, action_col2, action_col3 = st.columns(3)
            with action_col1:
                if st.button("Marcar como vendido", key=f"product-sold-{product['id']}"):
                    update_product_status(product["id"], "sold")
                    st.success(f"Produto {product['description']} marcado como vendido.")
                    st.rerun()
            with action_col2:
                if st.button("Marcar como promoção", key=f"product-promo-{product['id']}"):
                    update_product_status(product["id"], "promoted")
                    add_promotion(
                        product["barcode"],
                        "Produto cadastrado",
                        float(product.get("cost_price", 0.0) or 0.0),
                        date.today().isoformat(),
                        "Promoção registrada pelo painel de alertas",
                    )
                    st.success(f"Produto {product['description']} foi registrado para promoção.")
                    st.rerun()
            with action_col3:
                if st.button("Descartar", key=f"product-discard-{product['id']}"):
                    update_product_status(product["id"], "discarded")
                    st.warning(f"Produto {product['description']} marcado como descartado. Verifique o relatório de perdas.")
                    st.rerun()

        for batch in batches:
            expiry = date.fromisoformat(batch["expiry_date"])
            level = get_alert_level(expiry)
            color = {
                "expired": "#ff4d4d",
                "critical": "#ffb84d",
                "warning": "#ffd966",
                "attention": "#7ad9ff",
                "healthy": "#7fe98f",
            }.get(level, "#d9d9d9")
            st.markdown(
                f"<div style='background-color:{color}; color:#111827; padding:12px; border-radius:8px; margin-bottom:10px;'>"
                f"<strong>{batch['description']}</strong> | Lote {batch['batch_number']} | Validade: {batch['expiry_date']} | Status: {status_labels.get(batch['status'], batch['status'])} | Nível: {level_labels.get(level, level)}</div>",
                unsafe_allow_html=True,
            )
            action_col1, action_col2, action_col3 = st.columns(3)
            with action_col1:
                if st.button("Marcar como vendido", key=f"sold-{batch['id']}"):
                    update_batch_status(batch["id"], "sold")
                    st.success(f"Produto {batch['description']} marcado como vendido.")
                    st.rerun()
            with action_col2:
                if st.button("Marcar como promoção", key=f"promo-{batch['id']}"):
                    update_batch_status(batch["id"], "promoted")
                    add_promotion(
                        batch["barcode"],
                        batch["batch_number"],
                        float(batch.get("cost_price", 0.0) or 0.0),
                        date.today().isoformat(),
                        "Promoção registrada pelo painel de alertas",
                    )
                    st.success(f"Produto {batch['description']} foi registrado para promoção.")
                    st.rerun()
            with action_col3:
                if st.button("Descartar", key=f"discard-{batch['id']}"):
                    update_batch_status(batch["id"], "discarded")
                    st.warning(f"Produto {batch['description']} marcado como descartado. Verifique o relatório de perdas.")
                    st.rerun()

elif page == "Promoção":
    st.subheader("Registrar promoção")
    with st.form("promotion_form"):
        barcode = st.text_input("Código de barras do produto")
        batch_number = st.text_input("Lote")
        new_sale_price = st.number_input("Novo valor de venda", min_value=0.0, step=0.01)
        promotion_date = st.date_input("Data da promoção")
        notes = st.text_input("Observações")
        submitted = st.form_submit_button("Salvar promoção")
        if submitted:
            if not barcode:
                st.warning("Informe o código de barras.")
            else:
                add_promotion(barcode, batch_number, float(new_sale_price), promotion_date.isoformat(), notes)
                st.success("Promoção registrada com sucesso.")

    st.subheader("Promoções registradas")
    promotions = get_promotions()
    if promotions:
        translated_promotions = [
            {
                "ID": item["id"],
                "Código de barras": item["barcode"],
                "Descrição": item["description"],
                "Lote": item["batch_number"],
                "Novo valor": item["new_sale_price"],
                "Data da promoção": item["promotion_date"],
                "Observações": item["notes"],
            }
            for item in promotions
        ]
        st.dataframe(translated_promotions, use_container_width=True)
    else:
        st.info("Ainda não há promoções registradas.")

elif page == "Relatório de perdas":
    st.subheader("Relatório de perdas")
    start_date = st.date_input("Data inicial")
    end_date = st.date_input("Data final")
    report_type = st.selectbox("Tipo de relatório", ["Perdas", "Para descarte"])
    if st.button("Pesquisar"):
        if start_date <= end_date:
            if report_type == "Perdas":
                report = get_loss_report(start_date.isoformat(), end_date.isoformat())
                if report:
                    translated_report = [
                        {
                            "Categoria": item["category"],
                            "Valor total descartado": item["total_loss"],
                            "Data do descarte": item["discard_date"],
                        }
                        for item in report
                    ]
                    st.dataframe(translated_report, use_container_width=True)
                else:
                    st.info("Nenhum item descartado no período selecionado.")
            else:
                report = get_status_report("discarded", start_date.isoformat(), end_date.isoformat())
                if report:
                    translated_report = [
                        {
                            "ID": item["id"],
                            "Lote": item.get("lot") or item.get("batch_number") or "-",
                            "Código": item["barcode"],
                            "Descrição": item["description"],
                            "Categoria": item["category"],
                            "Validade": item["expiry_date"],
                            "Status": item["status"],
                            "Data de descarte": item["reference_date"],
                        }
                        for item in report
                    ]
                    st.dataframe(translated_report, use_container_width=True)
                else:
                    st.info("Nenhum item para descarte no período selecionado.")
        else:
            st.warning("A data inicial deve ser anterior ou igual à data final.")
