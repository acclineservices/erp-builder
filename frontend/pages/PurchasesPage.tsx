import { useEffect, useState, type FormEvent } from "react";
import type { AccessibleCompany } from "../services/auth";
import { caughtErrorMessage } from "../services/api";
import { partiesApi, type Party } from "../services/parties";
import { itemsApi, type Item } from "../services/items";
import { purchasesApi, type PurchaseDocument } from "../services/purchases";

type Tab = "orders" | "receipts" | "invoices";
type Load<T> = { state: "loading" | "ready" | "error"; data: T; message?: string };
const loading = <T,>(data: T): Load<T> => ({ state: "loading", data });
const today = () => new Date().toISOString().slice(0, 10);

export function PurchasesPage({ company }: { company?: AccessibleCompany }) {
  const companyId = company?.id ?? "";
  const [tab, setTab] = useState<Tab>("orders");
  const [refresh, setRefresh] = useState(0);
  const [suppliers, setSuppliers] = useState<Load<Party[]>>(loading([]));
  const [items, setItems] = useState<Load<Item[]>>(loading([]));
  const [orders, setOrders] = useState<Load<PurchaseDocument[]>>(loading([]));
  const [receipts, setReceipts] = useState<Load<PurchaseDocument[]>>(loading([]));
  const [invoices, setInvoices] = useState<Load<PurchaseDocument[]>>(loading([]));
  const [show, setShow] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);
  const reload = () => setRefresh((value) => value + 1);

  useEffect(() => {
    let current = true;
    setShow(false); setNotice(null);
    if (!companyId) return () => { current = false; };
    setSuppliers(loading([])); setItems(loading([])); setOrders(loading([])); setReceipts(loading([])); setInvoices(loading([]));
    const load = <T,>(request: Promise<T>, set: (value: Load<T>) => void, fallback: string) => {
      void request.then((data) => { if (current) set({ state: "ready", data }); }).catch((error: unknown) => {
        if (current) set({ state: "error", data: ([] as unknown as T), message: caughtErrorMessage(error, fallback) });
      });
    };
    load(partiesApi.list("supplier", companyId, { active: "true" }), setSuppliers, "Unable to load suppliers. Please try again.");
    load(itemsApi.items(companyId, { active: "true" }), setItems, "Unable to load items. Please try again.");
    load(purchasesApi.orders(companyId), setOrders, "Unable to load purchase orders. Please try again.");
    load(purchasesApi.receipts(companyId), setReceipts, "Unable to load goods receipts. Please try again.");
    load(purchasesApi.invoices(companyId), setInvoices, "Unable to load purchase invoices. Please try again.");
    return () => { current = false; };
  }, [companyId, refresh]);

  if (!company) return <section className="organization-empty"><h1>Purchases</h1><p>Select a company first.</p></section>;
  const documents = tab === "orders" ? orders : tab === "receipts" ? receipts : invoices;
  async function action(document: PurchaseDocument, action: string) {
    try {
      if (tab === "orders") await purchasesApi.orderAction(companyId, document.id, action);
      else if (tab === "invoices") await purchasesApi.invoiceAction(companyId, document.id, action);
      else await purchasesApi.cancelReceipt(companyId, document.id);
      setNotice("Purchase document updated."); reload();
    } catch (error) { setNotice(caughtErrorMessage(error, "Purchase document could not be updated.")); }
  }
  return <div className="page-stack organization-page party-page"><section className="organization-hero"><div><p className="section-kicker">Purchase workspace</p><h1>Purchases</h1><p>Create tenant-scoped orders, goods receipts, and purchase invoices.</p></div><button className="primary-action" onClick={() => setShow(true)}>New {tab === "orders" ? "purchase order" : tab === "receipts" ? "goods receipt" : "purchase invoice"}</button></section><div className="organization-tabs"><button className={tab === "orders" ? "selected" : ""} onClick={() => setTab("orders")}>Purchase Orders</button><button className={tab === "receipts" ? "selected" : ""} onClick={() => setTab("receipts")}>Goods Receipts</button><button className={tab === "invoices" ? "selected" : ""} onClick={() => setTab("invoices")}>Purchase Invoices</button></div>{notice && <p className="notice">{notice}</p>}<section className="organization-card administration-card">{show && <PurchaseForm tab={tab} suppliers={suppliers} items={items} orders={orders.data} companyId={companyId} done={() => { setShow(false); setNotice("Purchase document saved."); reload(); }} cancel={() => setShow(false)} />}{documents.state === "error" && <p className="notice error">{documents.message ?? "Unable to load purchase data. Please try again."}</p>}<div className="party-list">{documents.state === "loading" ? <p className="muted">Loading purchase documents…</p> : documents.data.map((document) => <article className="party-row" key={document.id}><div><strong>{document.number} · {document.supplier_name}</strong><p>{document.lines.length} line(s) · Total {document.grand_total ?? "—"}</p></div><div className="location-actions"><span className="status-badge active">{document.status}</span>{document.status === "draft" && tab === "orders" && <><button className="secondary-action" onClick={() => void action(document, "submit")}>Submit</button><button className="secondary-action" onClick={() => void action(document, "cancel")}>Cancel</button></>}{document.status === "submitted" && tab === "orders" && <button className="secondary-action" onClick={() => void action(document, "approve")}>Approve</button>}{document.status === "draft" && tab === "invoices" && <><button className="secondary-action" onClick={() => void action(document, "approve")}>Approve</button><button className="secondary-action" onClick={() => void action(document, "cancel")}>Cancel</button></>}{document.status !== "cancelled" && tab === "receipts" && <button className="secondary-action" onClick={() => void action(document, "cancel")}>Cancel</button>}</div></article>)}{documents.state === "ready" && !documents.data.length && !show && <p className="muted">No {tab} for this company yet.</p>}</div></section></div>;
}

function selectMessage<T>(resource: Load<T[]>, noun: string) {
  if (resource.state === "loading") return `Loading active ${noun}…`;
  if (resource.state === "error") return resource.message ?? `Unable to load ${noun}. Please try again.`;
  return resource.data.length ? `Select ${noun.slice(0, -1)}` : `No active ${noun} are available for this company.`;
}

function PurchaseForm({ tab, suppliers, items, orders, companyId, done, cancel }: { tab: Tab; suppliers: Load<Party[]>; items: Load<Item[]>; orders: PurchaseDocument[]; companyId: string; done: () => void; cancel: () => void }) {
  const [error, setError] = useState<string | null>(null);
  const goods = items.data.filter((item) => tab !== "receipts" || item.item_type === "goods");
  const referencesReady = suppliers.state === "ready" && items.state === "ready" && suppliers.data.length > 0 && goods.length > 0;
  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); const form = new FormData(event.currentTarget); const item = String(form.get("item_id")); const quantity = Number(form.get("quantity")); const rate = Number(form.get("rate")); const supplier_id = String(form.get("supplier_id"));
    try {
      if (tab === "orders") await purchasesApi.createOrder(companyId, { supplier_id, order_date: String(form.get("date")), payment_terms: null, round_off: 0, lines: [{ item_id: item, quantity, unit_rate: rate, discount_percent: 0, gst_rate: null }] });
      if (tab === "receipts") await purchasesApi.createReceipt(companyId, { supplier_id, purchase_order_id: String(form.get("purchase_order_id")) || null, warehouse_id: null, receipt_date: String(form.get("date")), lines: [{ item_id: item, received_quantity: quantity, accepted_quantity: quantity, rejected_quantity: 0 }] });
      if (tab === "invoices") await purchasesApi.createInvoice(companyId, { supplier_id, purchase_order_id: null, goods_receipt_id: null, supplier_invoice_number: String(form.get("supplier_invoice_number")), supplier_invoice_date: String(form.get("date")), document_date: String(form.get("date")), round_off: 0, lines: [{ item_id: item, quantity, unit_rate: rate, discount_percent: 0, gst_rate: null }] });
      done();
    } catch (exception) { setError(caughtErrorMessage(exception, "Purchase document could not be saved.")); }
  }
  return <form className="inline-form party-form" onSubmit={save}><h3>New {tab === "orders" ? "purchase order" : tab === "receipts" ? "goods receipt" : "purchase invoice"}</h3>{error && <p className="notice error">{error}</p>}<fieldset><legend>Document details</legend><label>Supplier<select name="supplier_id" required disabled={suppliers.state !== "ready" || !suppliers.data.length}><option value="">{selectMessage(suppliers, "suppliers")}</option>{suppliers.data.map((supplier) => <option key={supplier.id} value={supplier.id}>{supplier.display_name}</option>)}</select>{suppliers.state === "error" && <small>{suppliers.message}</small>}</label><label>Date<input name="date" type="date" defaultValue={today()} required /></label>{tab === "invoices" && <label>Supplier invoice number<input name="supplier_invoice_number" required /></label>}{tab === "receipts" && <label>Purchase order<select name="purchase_order_id"><option value="">Not linked</option>{orders.map((order) => <option key={order.id} value={order.id}>{order.number}</option>)}</select></label>}</fieldset><fieldset><legend>Line item</legend><label>Item<select name="item_id" required disabled={items.state !== "ready" || !goods.length}><option value="">{selectMessage({ ...items, data: goods }, "items")}</option>{goods.map((item) => <option key={item.id} value={item.id}>{item.code} · {item.name}</option>)}</select>{items.state === "error" && <small>{items.message}</small>}</label><label>Quantity<input name="quantity" type="number" min="0.001" step="0.001" defaultValue="1" required /></label>{tab !== "receipts" && <label>Unit rate<input name="rate" type="number" min="0" step="0.01" defaultValue="0" required /></label>}</fieldset><div className="form-actions"><button className="primary-action" disabled={!referencesReady}>Save draft</button><button className="secondary-action" type="button" onClick={cancel}>Cancel</button></div>{!referencesReady && <p className="muted">{suppliers.state === "loading" || items.state === "loading" ? "Loading required supplier and item data…" : "A supplier and item are required before this document can be saved."}</p>}</form>;
}
