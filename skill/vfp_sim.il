;; =====================================================================
;; vfp_sim.il — simulation pre-flight: dirty-check + inputs fingerprint
;; ---------------------------------------------------------------------
;; The single most expensive sim failure is running on a STALE netlist:
;; the schematic was edited but not saved, so createNetlist either fails
;; or silently reuses yesterday's deck (the 996µA ghost-regression chain).
;; Only the in-Virtuoso plugin can see a cellview's unsaved state, so the
;; dirty-check lives here and gates every netlist/job.
;;
;;   vfpCellViewDirty(cv)        unsaved changes on this cellview?
;;   vfpCellViewDirtyHier(cv)    ...or on any open sub-master
;;   vfpInputsFingerprint(cv t)  content digest (params+conn+test) — the
;;                               authoritative fingerprint the tunnel's
;;                               freshness guard reuses (its own fallback
;;                               keys on lib/cell/view+test only, so an
;;                               edited param would wrongly reuse a result)
;;   vfpSimPreflight(cv t)       {ready, dirty, cellview, fingerprint, reason}
;;
;; Loaded after vfp_connectivity.il (uses vfpCvId / vfpJObj / vfpToStr).
;; =====================================================================

;; Unsaved changes on this cellview? dbIsCellViewModified is true from the
;; first edit until save (and flips back to nil when every change is undone).
defun( vfpCellViewDirty (cv)
  and( cv car(errset( dbIsCellViewModified(cv) )) t )
)

;; Dirty including the hierarchy: the target cellview, or any of its
;; instance masters that are open and modified (a sub-circuit edited but
;; not saved would netlist stale just the same). PDK device masters are
;; read-only and never report dirty, so they cost nothing here.
defun( vfpCellViewDirtyHier (cv)
  or( vfpCellViewDirty(cv)
      and( cv
           exists( inst cv~>instances
                   vfpCellViewDirty(inst~>master) ) ) )
)

;; Canonical content string of the design inputs: the test name, every
;; instance terminal's net, and every CDF parameter value, each list
;; sorted so the string is order-independent. Identical design inputs =>
;; identical string; any param or wire change moves it. Fed verbatim to
;; job.create as inputs_fingerprint (the freshness guard compares by ==).
defun( vfpInputsFingerprint (cv @optional (test ""))
  let( (terms params)
    terms = nil
    when( cv
      foreach( inst cv~>instances
        foreach( it inst~>instTerms
          terms = cons( sprintf(nil "%s.%s=%s" inst~>name it~>term~>name
                          if(it~>net it~>net~>name "")) terms ) ) ) )
    terms = sort(terms 'alphalessp)
    params = nil
    when( cv
      foreach( inst cv~>instances
        let( (cdf) cdf = car(errset( cdfGetInstCDF(inst) ))
          when( cdf
            foreach( p cdf~>parameters
              params = cons( sprintf(nil "%s.%s=%s" inst~>name p~>name
                               vfpToStr(p~>value)) params ) ) ) ) ) )
    params = sort(params 'alphalessp)
    sprintf(nil "test=%s;conn=%s;params=%s"
      vfpToStr(test) buildString(terms "|") buildString(params "|"))
  )
)

;; Pre-flight a netlist/sim of `cv`: bundle the dirty verdict, the inputs
;; fingerprint, and a ready flag. ready is nil when the cellview is dirty,
;; with a reason that names the cellview (so the caller can refuse the
;; netlist or save first — never silently netlist a stale schematic).
defun( vfpSimPreflight (cv @optional (test ""))
  let( (cvid dirty)
    cvid  = vfpCvId(cv)
    dirty = vfpCellViewDirtyHier(cv)
    list(
      list("ready"       if(dirty nil t))
      list("dirty"       if(dirty t nil))
      list("cellview"    cvid)
      list("fingerprint" vfpInputsFingerprint(cv test))
      list("reason"      if(dirty
                            sprintf(nil "%s has unsaved changes; save before netlisting" cvid)
                            ""))
    )
  )
)

;; JSON object form of the pre-flight (for context export / a sim RPC).
defun( vfpSimPreflightJson (cv @optional (test ""))
  let( (pf)
    pf = vfpSimPreflight(cv test)
    vfpJObj(
      "ready"       if(vfpAlistGet(pf "ready") 'true 'false)
      "dirty"       if(vfpAlistGet(pf "dirty") 'true 'false)
      "cellview"    vfpAlistGet(pf "cellview")
      "fingerprint" vfpAlistGet(pf "fingerprint")
      "reason"      vfpAlistGet(pf "reason")
    )
  )
)
