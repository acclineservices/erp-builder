import { useEffect, useState, type FormEvent } from "react";

import type { AccessibleCompany } from "../services/auth";
import {
  organizationApi,
  selectedCompanyName,
  type Branch,
  type BranchInput,
  type CompanyProfile,
  type CompanyUpdate,
  type Warehouse,
  type WarehouseInput,
} from "../services/organization";

type Tab = "company" | "branches" | "warehouses";
type Notice = { kind: "success" | "error"; text: string } | null;

const blankAddress = { address_line1: null, address_line2: null, city: null, state: null, postal_code: null, country: null };
const blankBranch = (): BranchInput => ({ name: "", code: null, email: null, phone: null, ...blankAddress });
const blankWarehouse = (): WarehouseInput => ({ name: "", code: null, branch_id: null, contact_person: null, contact_number: null, ...blankAddress });

function text(value: string | null | undefined) { return value ?? ""; }
function nullable(value: FormDataEntryValue | null): string | null { const trimmed = String(value ?? "").trim(); return trimmed || null; }

export function OrganizationPage({ company }: { company?: AccessibleCompany }) {
  const [tab, setTab] = useState<Tab>("company");
  const [profile, setProfile] = useState<CompanyProfile | null>(null);
  const [branches, setBranches] = useState<Branch[]>([]);
  const [warehouses, setWarehouses] = useState<Warehouse[]>([]);
  const [loading, setLoading] = useState(true);
  const [notice, setNotice] = useState<Notice>(null);

  useEffect(() => {
    if (!company) { setLoading(false); return; }
    let active = true;
    setLoading(true); setNotice(null); setProfile(null); setBranches([]); setWarehouses([]);
    Promise.all([organizationApi.company(company.id), organizationApi.branches(company.id), organizationApi.warehouses(company.id)])
      .then(([nextProfile, nextBranches, nextWarehouses]) => { if (active) { setProfile(nextProfile); setBranches(nextBranches); setWarehouses(nextWarehouses); } })
      .catch((error: Error) => active && setNotice({ kind: "error", text: error.message }))
      .finally(() => active && setLoading(false));
    return () => { active = false; };
  }, [company?.id]);

  if (!company) return <section className="organization-empty"><h1>Organization setup</h1><p>Select an authorized company to manage its profile and locations.</p></section>;
  if (loading) return <section className="organization-empty"><h1>Organization setup</h1><p>Loading the authorized {selectedCompanyName(company)} context…</p></section>;

  return <div className="page-stack organization-page">
    <section className="organization-hero"><div><p className="section-kicker">Organization</p><h1>Company setup</h1><p>Manage the profile and optional operating locations for {selectedCompanyName(company)}.</p></div>{profile && <div className="setup-progress"><strong>{profile.setup_progress}%</strong><span>profile complete</span><div><i style={{ width: `${profile.setup_progress}%` }} /></div></div>}</section>
    <nav className="organization-tabs" aria-label="Organization setup sections"><button className={tab === "company" ? "selected" : ""} onClick={() => setTab("company")}>Company profile</button><button className={tab === "branches" ? "selected" : ""} onClick={() => setTab("branches")}>Branches <span>{branches.length}</span></button><button className={tab === "warehouses" ? "selected" : ""} onClick={() => setTab("warehouses")}>Warehouses <span>{warehouses.length}</span></button></nav>
    {notice && <p className={`notice ${notice.kind}`}>{notice.text}</p>}
    {tab === "company" && profile && <CompanyForm profile={profile} onSave={async (payload) => { try { const next = await organizationApi.updateCompany(company.id, payload); setProfile(next); setNotice({ kind: "success", text: "Company profile saved." }); } catch (error) { setNotice({ kind: "error", text: (error as Error).message }); } }} />}
    {tab === "branches" && <BranchSection companyId={company.id} branches={branches} onChange={setBranches} onNotice={setNotice} />}
    {tab === "warehouses" && <WarehouseSection companyId={company.id} warehouses={warehouses} branches={branches} onChange={setWarehouses} onNotice={setNotice} />}
  </div>;
}

function CompanyForm({ profile, onSave }: { profile: CompanyProfile; onSave: (payload: CompanyUpdate) => Promise<void> }) {
  const [saving, setSaving] = useState(false);
  async function submit(event: FormEvent<HTMLFormElement>) { event.preventDefault(); setSaving(true); const form = new FormData(event.currentTarget); await onSave({ legal_name: nullable(form.get("legal_name")), display_name: nullable(form.get("display_name")), business_type: String(form.get("business_type") ?? "proprietorship"), gst_status: nullable(form.get("gst_status")), gstin: nullable(form.get("gstin")), email: nullable(form.get("email")), phone: nullable(form.get("phone")), logo_url: nullable(form.get("logo_url")), ...addressPayload(form) }); setSaving(false); }
  return <form className="organization-card organization-form" onSubmit={(event) => void submit(event)}><div className="card-heading"><div><p className="section-kicker">Company profile</p><h2>{profile.business_name}</h2><p>Subscription and company status are controlled by Accline Services. Logo storage is prepared as a URL field; upload storage is intentionally deferred.</p></div><StatusBadge active={profile.status === "active"} label={profile.status} /></div><fieldset><legend>Business identity</legend><Field name="legal_name" label="Legal name" value={text(profile.legal_name)} /><Field name="display_name" label="Display name" value={text(profile.display_name)} /><label>Business type<select name="business_type" defaultValue={profile.business_type}><option value="proprietorship">Proprietorship</option><option value="partnership">Partnership</option><option value="company">Company</option><option value="other">Other</option></select></label><Field name="logo_url" label="Logo URL (optional foundation)" value={text(profile.logo_url)} /></fieldset><fieldset><legend>Registration and contact</legend><Field name="gst_status" label="GST registration status (optional)" value={text(profile.gst_status)} /><Field name="gstin" label="GSTIN (optional)" value={text(profile.gstin)} /><Field name="email" label="Business email" value={text(profile.email)} type="email" /><Field name="phone" label="Business phone" value={text(profile.phone)} /></fieldset><AddressFields values={profile} /><div className="form-actions"><button type="submit" className="primary-action" disabled={saving}>{saving ? "Saving…" : "Save company profile"}</button></div></form>;
}

function BranchSection({ companyId, branches, onChange, onNotice }: { companyId: string; branches: Branch[]; onChange: (branches: Branch[]) => void; onNotice: (notice: Notice) => void }) {
  const [editing, setEditing] = useState<Branch | null>(null); const [adding, setAdding] = useState(false);
  async function save(payload: BranchInput) { try { const saved = editing ? await organizationApi.updateBranch(companyId, editing.id, payload) : await organizationApi.createBranch(companyId, payload); onChange(editing ? branches.map((item) => item.id === saved.id ? saved : item) : [...branches, saved]); setEditing(null); setAdding(false); onNotice({ kind: "success", text: editing ? "Branch updated." : "Branch created." }); } catch (error) { onNotice({ kind: "error", text: (error as Error).message }); } }
  async function toggle(branch: Branch) { if (!window.confirm(`${branch.is_active ? "Deactivate" : "Activate"} ${branch.name}?`)) return; try { const saved = await organizationApi.setBranchStatus(companyId, branch.id, !branch.is_active); onChange(branches.map((item) => item.id === saved.id ? saved : item)); onNotice({ kind: "success", text: `Branch ${saved.is_active ? "activated" : "deactivated"}.` }); } catch (error) { onNotice({ kind: "error", text: (error as Error).message }); } }
  return <section className="organization-card"><div className="card-heading"><div><p className="section-kicker">Optional operating locations</p><h2>Branches</h2><p>Companies can operate without branches. No head office branch is created automatically.</p></div><button className="primary-action" onClick={() => { setAdding(true); setEditing(null); }}>Add branch</button></div>{(adding || editing) && <BranchForm branch={editing} onCancel={() => { setAdding(false); setEditing(null); }} onSave={save} />}{!branches.length ? <EmptyState title="No branches yet" description="This company can operate directly without a branch. Add one only when a separate operating location is needed." /> : <div className="location-list">{branches.map((branch) => <LocationCard key={branch.id} title={branch.name} subtitle={[branch.code, branch.city, branch.state].filter(Boolean).join(" · ")} active={branch.is_active} onEdit={() => { setEditing(branch); setAdding(false); }} onToggle={() => void toggle(branch)} />)}</div>}</section>;
}

function WarehouseSection({ companyId, warehouses, branches, onChange, onNotice }: { companyId: string; warehouses: Warehouse[]; branches: Branch[]; onChange: (warehouses: Warehouse[]) => void; onNotice: (notice: Notice) => void }) {
  const [editing, setEditing] = useState<Warehouse | null>(null); const [adding, setAdding] = useState(false);
  async function save(payload: WarehouseInput) { try { const saved = editing ? await organizationApi.updateWarehouse(companyId, editing.id, payload) : await organizationApi.createWarehouse(companyId, payload); onChange(editing ? warehouses.map((item) => item.id === saved.id ? saved : item) : [...warehouses, saved]); setEditing(null); setAdding(false); onNotice({ kind: "success", text: editing ? "Warehouse updated." : "Warehouse created." }); } catch (error) { onNotice({ kind: "error", text: (error as Error).message }); } }
  async function toggle(warehouse: Warehouse) { if (!window.confirm(`${warehouse.is_active ? "Deactivate" : "Activate"} ${warehouse.name}?`)) return; try { const saved = await organizationApi.setWarehouseStatus(companyId, warehouse.id, !warehouse.is_active); onChange(warehouses.map((item) => item.id === saved.id ? saved : item)); onNotice({ kind: "success", text: `Warehouse ${saved.is_active ? "activated" : "deactivated"}.` }); } catch (error) { onNotice({ kind: "error", text: (error as Error).message }); } }
  return <section className="organization-card"><div className="card-heading"><div><p className="section-kicker">Optional inventory locations</p><h2>Warehouses</h2><p>Warehouses are optional and can be linked to a branch in this company when one exists.</p></div><button className="primary-action" onClick={() => { setAdding(true); setEditing(null); }}>Add warehouse</button></div>{(adding || editing) && <WarehouseForm warehouse={editing} branches={branches} onCancel={() => { setAdding(false); setEditing(null); }} onSave={save} />}{!warehouses.length ? <EmptyState title="No warehouses yet" description="Inventory can start without an explicit warehouse. Add one when stock needs a named location." /> : <div className="location-list">{warehouses.map((warehouse) => <LocationCard key={warehouse.id} title={warehouse.name} subtitle={[warehouse.code, branches.find((branch) => branch.id === warehouse.branch_id)?.name, warehouse.city].filter(Boolean).join(" · ")} active={warehouse.is_active} onEdit={() => { setEditing(warehouse); setAdding(false); }} onToggle={() => void toggle(warehouse)} />)}</div>}</section>;
}

function BranchForm({ branch, onSave, onCancel }: { branch: Branch | null; onSave: (payload: BranchInput) => Promise<void>; onCancel: () => void }) { const [saving, setSaving] = useState(false); async function submit(event: FormEvent<HTMLFormElement>) { event.preventDefault(); setSaving(true); const form = new FormData(event.currentTarget); await onSave({ name: String(form.get("name") ?? ""), code: nullable(form.get("code")), email: nullable(form.get("email")), phone: nullable(form.get("phone")), ...addressPayload(form) }); setSaving(false); } return <form className="inline-form" onSubmit={(event) => void submit(event)}><h3>{branch ? "Edit branch" : "New branch"}</h3><Field name="name" label="Branch name" value={text(branch?.name)} required /><Field name="code" label="Branch code" value={text(branch?.code)} /><Field name="email" label="Email" value={text(branch?.email)} type="email" /><Field name="phone" label="Phone" value={text(branch?.phone)} /><AddressFields values={branch ?? blankAddress} /><div className="form-actions"><button type="submit" className="primary-action" disabled={saving}>{saving ? "Saving…" : "Save branch"}</button><button type="button" className="secondary-action" onClick={onCancel}>Cancel</button></div></form>; }

function WarehouseForm({ warehouse, branches, onSave, onCancel }: { warehouse: Warehouse | null; branches: Branch[]; onSave: (payload: WarehouseInput) => Promise<void>; onCancel: () => void }) { const [saving, setSaving] = useState(false); async function submit(event: FormEvent<HTMLFormElement>) { event.preventDefault(); setSaving(true); const form = new FormData(event.currentTarget); await onSave({ name: String(form.get("name") ?? ""), code: nullable(form.get("code")), branch_id: nullable(form.get("branch_id")), contact_person: nullable(form.get("contact_person")), contact_number: nullable(form.get("contact_number")), ...addressPayload(form) }); setSaving(false); } return <form className="inline-form" onSubmit={(event) => void submit(event)}><h3>{warehouse ? "Edit warehouse" : "New warehouse"}</h3><Field name="name" label="Warehouse name" value={text(warehouse?.name)} required /><Field name="code" label="Warehouse code" value={text(warehouse?.code)} /><label>Associated branch (optional)<select name="branch_id" defaultValue={warehouse?.branch_id ?? ""}><option value="">No branch association</option>{branches.map((branch) => <option key={branch.id} value={branch.id}>{branch.name}{branch.is_active ? "" : " (inactive)"}</option>)}</select></label><Field name="contact_person" label="Contact person" value={text(warehouse?.contact_person)} /><Field name="contact_number" label="Contact number" value={text(warehouse?.contact_number)} /><AddressFields values={warehouse ?? blankAddress} /><div className="form-actions"><button type="submit" className="primary-action" disabled={saving}>{saving ? "Saving…" : "Save warehouse"}</button><button type="button" className="secondary-action" onClick={onCancel}>Cancel</button></div></form>; }

function AddressFields({ values }: { values: Partial<{ address_line1: string | null; address_line2: string | null; city: string | null; state: string | null; postal_code: string | null; country: string | null }> }) { return <fieldset><legend>Address</legend><Field name="address_line1" label="Address line 1" value={text(values.address_line1)} /><Field name="address_line2" label="Address line 2" value={text(values.address_line2)} /><Field name="city" label="City" value={text(values.city)} /><Field name="state" label="State" value={text(values.state)} /><Field name="postal_code" label="Postal code" value={text(values.postal_code)} /><Field name="country" label="Country" value={text(values.country)} /></fieldset>; }

function addressPayload(form: FormData) { return { address_line1: nullable(form.get("address_line1")), address_line2: nullable(form.get("address_line2")), city: nullable(form.get("city")), state: nullable(form.get("state")), postal_code: nullable(form.get("postal_code")), country: nullable(form.get("country")) }; }
function Field({ name, label, value, required = false, type = "text" }: { name: string; label: string; value: string; required?: boolean; type?: string }) { return <label>{label}<input name={name} type={type} defaultValue={value} required={required} /></label>; }
function StatusBadge({ active, label }: { active: boolean; label: string }) { return <span className={`status-badge ${active ? "active" : "inactive"}`}>{label}</span>; }
function EmptyState({ title, description }: { title: string; description: string }) { return <div className="empty-state"><strong>{title}</strong><p>{description}</p></div>; }
function LocationCard({ title, subtitle, active, onEdit, onToggle }: { title: string; subtitle: string; active: boolean; onEdit: () => void; onToggle: () => void }) { return <article className="location-card"><div><h3>{title}</h3><p>{subtitle || "No location details yet"}</p></div><div className="location-actions"><StatusBadge active={active} label={active ? "Active" : "Inactive"} /><button className="secondary-action" onClick={onEdit}>Edit</button><button className="secondary-action" onClick={onToggle}>{active ? "Deactivate" : "Activate"}</button></div></article>; }
