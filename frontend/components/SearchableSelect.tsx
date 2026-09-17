import { useMemo, useState } from "react";

export type SearchOption = { value: string; label: string; search: string };

/** Lightweight, reusable searchable selector for company-scoped master data. */
export function SearchableSelect({ value, options, placeholder, disabled, onChange }: { value: string; options: SearchOption[]; placeholder: string; disabled?: boolean; onChange: (value: string) => void }) {
  const [query, setQuery] = useState("");
  const [open, setOpen] = useState(false);
  const matches = useMemo(() => options.filter((option) => option.search.toLowerCase().includes(query.toLowerCase())).slice(0, 12), [options, query]);
  const selected = options.find((option) => option.value === value);
  return <div className="searchable-select"><input aria-label={placeholder} value={open ? query : selected?.label ?? ""} placeholder={placeholder} disabled={disabled} onFocus={() => { setOpen(true); setQuery(""); }} onChange={(event) => { setOpen(true); setQuery(event.target.value); if (!event.target.value) onChange(""); }} onKeyDown={(event) => { if (event.key === "Escape") setOpen(false); if (event.key === "Enter" && matches.length === 1) { event.preventDefault(); onChange(matches[0].value); setOpen(false); } }} />{open && !disabled && <div className="searchable-options" role="listbox">{matches.length ? matches.map((option) => <button type="button" role="option" key={option.value} onMouseDown={(event) => event.preventDefault()} onClick={() => { onChange(option.value); setOpen(false); }}>{option.label}</button>) : <p>No matching active records.</p>}</div>}</div>;
}
