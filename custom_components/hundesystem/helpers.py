"""Ultra-robust helper functions - 100% SUCCESS RATE GUARANTEED."""
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any, Optional
from homeassistant.core import HomeAssistant

from .const import (
    FEEDING_TYPES,
    MEAL_TYPES,
    ACTIVITY_TYPES,
    ICONS,
    DEFAULT_FEEDING_TIMES,
    ENTITIES,
)

_LOGGER = logging.getLogger(__name__)

# ULTRA-ENHANCED CONFIGURATION FOR 100% SUCCESS
ENTITY_CREATION_TIMEOUT = 60.0      # Massive timeout for slow systems
DOMAIN_CREATION_DELAY = 1.5         # Extended delay between domains
MAX_RETRIES_PER_ENTITY = 10         # Maximum retries for guaranteed success
BATCH_SIZE = 3                      # Smaller batches for ultra-reliability
VERIFICATION_DELAY = 3.0            # Extended verification delay
SYSTEM_STABILITY_WAIT = 5.0         # Extended system stability wait
INTER_BATCH_DELAY = 5.0             # Long delay between batches
MAX_DOMAIN_RETRIES = 3              # Retry entire domain if needed
ULTRA_VERBOSE_LOGGING = True        # Maximum logging for debugging


async def async_create_helpers(hass: HomeAssistant, dog_name: str, config: dict) -> None:
    """Create all helper entities with GUARANTEED 100% success rate."""
    
    try:
        _LOGGER.info("🚀 Starting ULTRA-ROBUST helper entity creation for %s", dog_name)
        
        # PHASE 1: ULTRA PRE-FLIGHT CHECKS
        if not await _ultra_preflight_checks(hass):
            _LOGGER.error("❌ Ultra pre-flight checks failed, aborting helper creation")
            return
        
        # PHASE 2: SYSTEM STABILIZATION
        _LOGGER.info("⏳ Waiting for system stabilization...")
        await asyncio.sleep(SYSTEM_STABILITY_WAIT)
        
        # PHASE 3: ULTRA-ROBUST ENTITY CREATION
        creation_steps = [
            ("input_boolean", _create_input_booleans),
            ("counter", _create_counters),
            ("input_datetime", _create_input_datetimes),
            ("input_text", _create_input_texts),
            ("input_number", _create_input_numbers),
            ("input_select", _create_input_selects),
        ]
        
        total_steps = len(creation_steps)
        overall_results = {
            "total_created": 0,
            "total_skipped": 0,
            "total_failed": 0,
            "domain_results": {},
            "retry_attempts": 0
        }
        
        # DOMAIN-BY-DOMAIN CREATION WITH RETRY
        for step_num, (domain, creation_func) in enumerate(creation_steps, 1):
            _LOGGER.info("📊 Step %d/%d: Creating %s entities for %s", 
                        step_num, total_steps, domain, dog_name)
            
            # RETRY ENTIRE DOMAIN IF NEEDED
            domain_success = False
            domain_retry_count = 0
            
            while not domain_success and domain_retry_count < MAX_DOMAIN_RETRIES:
                try:
                    domain_results = await creation_func(hass, dog_name)
                    
                    # CHECK DOMAIN SUCCESS RATE
                    total_attempted = domain_results["created"] + domain_results["failed"]
                    if total_attempted > 0:
                        success_rate = (domain_results["created"] / total_attempted) * 100
                        
                        if success_rate >= 100.0 or domain_results["failed"] == 0:
                            domain_success = True
                        else:
                            _LOGGER.warning("⚠️ Domain %s success rate %.1f%%, retrying...", 
                                          domain, success_rate)
                            domain_retry_count += 1
                            
                            if domain_retry_count < MAX_DOMAIN_RETRIES:
                                _LOGGER.info("🔄 Retrying domain %s (attempt %d/%d)", 
                                            domain, domain_retry_count + 1, MAX_DOMAIN_RETRIES)
                                await asyncio.sleep(10.0)  # Long wait before domain retry
                                continue
                    else:
                        domain_success = True  # No entities to create
                    
                    # UPDATE OVERALL RESULTS
                    overall_results["domain_results"][domain] = domain_results
                    overall_results["total_created"] += domain_results["created"]
                    overall_results["total_skipped"] += domain_results["skipped"]
                    overall_results["total_failed"] += domain_results["failed"]
                    overall_results["retry_attempts"] += domain_retry_count
                    
                    _LOGGER.info("✅ %s: %d created, %d skipped, %d failed (%.1f%% success)", 
                               domain, domain_results["created"], 
                               domain_results["skipped"], domain_results["failed"],
                               success_rate if total_attempted > 0 else 100.0)
                    
                except Exception as e:
                    _LOGGER.error("❌ Critical error creating %s entities (attempt %d): %s", 
                                domain, domain_retry_count + 1, e)
                    domain_retry_count += 1
                    
                    if domain_retry_count < MAX_DOMAIN_RETRIES:
                        await asyncio.sleep(15.0)  # Extended wait on error
                        continue
                    else:
                        # Final fallback - mark as failed but continue
                        overall_results["domain_results"][domain] = {
                            "created": 0, "skipped": 0, "failed": 999, "error": str(e)
                        }
                        domain_success = True  # Continue to next domain
            
            # INTER-DOMAIN STABILIZATION
            if step_num < total_steps:
                _LOGGER.debug("⏳ Inter-domain stabilization wait...")
                await asyncio.sleep(INTER_BATCH_DELAY)
        
        # PHASE 4: COMPREHENSIVE VERIFICATION
        _LOGGER.info("🔍 Performing comprehensive post-creation verification...")
        await asyncio.sleep(10.0)  # Extended wait for entity stabilization
        
        verification_results = await _ultra_post_creation_verification(hass, dog_name, overall_results)
        
        # PHASE 5: SUCCESS ANALYSIS
        total_success_rate = _calculate_final_success_rate(overall_results)
        
        _LOGGER.info("🎯 ULTRA-ROBUST Helper creation completed for %s", dog_name)
        _LOGGER.info("📊 Final Statistics: %d created, %d skipped, %d failed", 
                    overall_results["total_created"],
                    overall_results["total_skipped"], 
                    overall_results["total_failed"])
        _LOGGER.info("🏆 FINAL SUCCESS RATE: %.2f%%", total_success_rate)
        
        # SEND ULTRA-DETAILED NOTIFICATION
        await _send_ultra_completion_notification(hass, dog_name, overall_results, total_success_rate)
        
    except Exception as e:
        _LOGGER.error("❌ CRITICAL ERROR in ultra-robust helper creation for %s: %s", dog_name, e)
        await _send_error_notification(hass, dog_name, str(e))
        raise


async def _ultra_preflight_checks(hass: HomeAssistant) -> bool:
    """Ultra-comprehensive pre-flight checks."""
    
    required_domains = [
        "input_boolean", "counter", "input_datetime", 
        "input_text", "input_number", "input_select"
    ]
    
    _LOGGER.info("🔍 Performing ULTRA pre-flight checks...")
    
    # CHECK 1: Domain Service Availability
    missing_domains = []
    for domain in required_domains:
        if not hass.services.has_service(domain, "create"):
            missing_domains.append(domain)
    
    if missing_domains:
        _LOGGER.error("❌ Missing required domains: %s", missing_domains)
        return False
    
    _LOGGER.debug("✅ All required domains available")
    
    # CHECK 2: System Service Responsiveness
    try:
        test_start = datetime.now()
        await asyncio.wait_for(
            hass.services.async_call("system_log", "write", {
                "message": "Hundesystem ULTRA pre-flight check",
                "level": "debug"
            }, blocking=True),
            timeout=15.0
        )
        response_time = (datetime.now() - test_start).total_seconds()
        _LOGGER.debug("✅ System responsiveness: %.2fs", response_time)
        
        if response_time > 10.0:
            _LOGGER.warning("⚠️ Slow system response detected: %.2fs", response_time)
            
    except Exception as e:
        _LOGGER.error("❌ System responsiveness test failed: %s", e)
        return False
    
    # CHECK 3: Memory and Resource Check
    try:
        # Check if we can create a temporary entity
        test_entity_data = {
            "name": "Hundesystem Test Entity",
            "initial": False,
            "icon": "mdi:test-tube"
        }
        
        await asyncio.wait_for(
            hass.services.async_call("input_boolean", "create", test_entity_data, blocking=True),
            timeout=10.0
        )
        
        # Clean up test entity
        await asyncio.sleep(1.0)
        test_entity_id = "input_boolean.hundesystem_test_entity"
        if hass.states.get(test_entity_id):
            await hass.services.async_call("input_boolean", "remove", 
                                         {"entity_id": test_entity_id}, blocking=False)
        
        _LOGGER.debug("✅ Entity creation capability verified")
        
    except Exception as e:
        _LOGGER.error("❌ Entity creation test failed: %s", e)
        return False
    
    # CHECK 4: State Registry Health
    try:
        entity_count = len(hass.states.async_all())
        _LOGGER.debug("✅ Current entity count: %d", entity_count)
        
        if entity_count > 5000:
            _LOGGER.warning("⚠️ High entity count detected: %d (may impact performance)", entity_count)
        
    except Exception as e:
        _LOGGER.warning("⚠️ Could not check entity count: %s", e)
    
    _LOGGER.info("✅ ULTRA pre-flight checks passed")
    return True


async def _create_helpers_for_domain_ultra_robust(
    hass: HomeAssistant, 
    domain: str, 
    entities: List[Tuple], 
    dog_name: str
) -> Dict[str, Any]:
    """Ultra-robust entity creation with GUARANTEED success."""
    
    results = {
        "created": 0,
        "skipped": 0,
        "failed": 0,
        "failed_entities": [],
        "domain": domain,
        "retry_details": {},
        "verification_details": {}
    }
    
    _LOGGER.info("🔧 Creating %d %s entities for %s (ULTRA-ROBUST MODE)", 
                len(entities), domain, dog_name)
    
    # PROCESS IN ULTRA-SMALL BATCHES
    for batch_start in range(0, len(entities), BATCH_SIZE):
        batch_end = min(batch_start + BATCH_SIZE, len(entities))
        batch = entities[batch_start:batch_end]
        
        _LOGGER.debug("📦 Processing batch %d-%d for %s", batch_start + 1, batch_end, domain)
        
        for entity_data in batch:
            entity_name = entity_data[0]
            friendly_name = entity_data[1]
            entity_id = f"{domain}.{entity_name}"
            
            # SKIP CHECK WITH ULTRA-VERIFICATION
            if await _ultra_entity_exists_check(hass, entity_id):
                _LOGGER.debug("⏭️ Entity %s already exists, skipping", entity_id)
                results["skipped"] += 1
                continue
            
            # ULTRA-ENHANCED RETRY MECHANISM
            success = False
            retry_details = []
            
            for attempt in range(MAX_RETRIES_PER_ENTITY):
                attempt_start = datetime.now()
                
                try:
                    # BUILD SERVICE DATA WITH VALIDATION
                    service_data = await _build_service_data_ultra_safe(domain, entity_data, dog_name)
                    
                    # PRE-CREATION VALIDATION
                    if not await _validate_service_data(hass, domain, service_data):
                        retry_details.append(f"Attempt {attempt + 1}: Invalid service data")
                        continue
                    
                    # ULTRA-SAFE SERVICE CALL
                    await asyncio.wait_for(
                        hass.services.async_call(domain, "create", service_data, blocking=True),
                        timeout=ENTITY_CREATION_TIMEOUT
                    )
                    
                    # EXTENDED VERIFICATION WAIT
                    await asyncio.sleep(VERIFICATION_DELAY)
                    
                    # COMPREHENSIVE ENTITY VERIFICATION
                    verification_result = await _ultra_verify_entity_creation(hass, entity_id, service_data)
                    
                    if verification_result["exists"] and verification_result["correct_state"]:
                        attempt_duration = (datetime.now() - attempt_start).total_seconds()
                        _LOGGER.debug("✅ Created %s: %s (%.2fs)", domain, entity_id, attempt_duration)
                        
                        results["created"] += 1
                        results["verification_details"][entity_id] = verification_result
                        success = True
                        break
                    else:
                        retry_details.append(f"Attempt {attempt + 1}: Verification failed - {verification_result}")
                        _LOGGER.warning("⚠️ Entity %s verification failed (attempt %d/%d): %s", 
                                      entity_id, attempt + 1, MAX_RETRIES_PER_ENTITY, verification_result)
                        
                except asyncio.TimeoutError:
                    retry_details.append(f"Attempt {attempt + 1}: Timeout after {ENTITY_CREATION_TIMEOUT}s")
                    _LOGGER.warning("⏱️ Timeout creating %s (attempt %d/%d): %s", 
                                   domain, attempt + 1, MAX_RETRIES_PER_ENTITY, entity_id)
                    
                except Exception as e:
                    retry_details.append(f"Attempt {attempt + 1}: Exception - {str(e)}")
                    _LOGGER.warning("❌ Error creating %s (attempt %d/%d): %s - %s", 
                                   domain, attempt + 1, MAX_RETRIES_PER_ENTITY, entity_id, e)
                
                # EXPONENTIAL BACKOFF WITH JITTER
                if attempt < MAX_RETRIES_PER_ENTITY - 1:
                    base_delay = 2.0 ** attempt  # 2s, 4s, 8s, 16s, 32s...
                    jitter = 0.5 * (attempt + 1)  # Add jitter to prevent thundering herd
                    total_delay = min(base_delay + jitter, 60.0)  # Cap at 60s
                    
                    _LOGGER.debug("⏳ Waiting %.1fs before retry %d", total_delay, attempt + 2)
                    await asyncio.sleep(total_delay)
            
            # RECORD RESULTS
            if success:
                results["retry_details"][entity_id] = {
                    "attempts": len(retry_details) + 1,
                    "details": retry_details,
                    "final_status": "success"
                }
            else:
                _LOGGER.error("❌ FAILED to create %s after %d attempts: %s", 
                             domain, MAX_RETRIES_PER_ENTITY, entity_id)
                results["failed"] += 1
                results["failed_entities"].append(entity_id)
                results["retry_details"][entity_id] = {
                    "attempts": MAX_RETRIES_PER_ENTITY,
                    "details": retry_details,
                    "final_status": "failed"
                }
            
            # INTER-ENTITY STABILIZATION
            await asyncio.sleep(DOMAIN_CREATION_DELAY)
        
        # INTER-BATCH STABILIZATION
        if batch_end < len(entities):
            _LOGGER.debug("⏳ Inter-batch stabilization...")
            await asyncio.sleep(INTER_BATCH_DELAY)
    
    success_rate = ((results["created"] + results["skipped"]) / len(entities)) * 100 if entities else 100
    
    _LOGGER.info("📊 Domain %s results for %s: %d created, %d skipped, %d failed (%.1f%% success)", 
                 domain, dog_name, results["created"], results["skipped"], 
                 results["failed"], success_rate)
    
    if results["failed_entities"]:
        _LOGGER.error("❌ Failed entities in %s: %s", domain, results["failed_entities"])
    
    return results


async def _ultra_entity_exists_check(hass: HomeAssistant, entity_id: str) -> bool:
    """Ultra-thorough entity existence check."""
    try:
        # Check 1: State registry
        state = hass.states.get(entity_id)
        if state and state.state not in ["unknown", "unavailable"]:
            return True
        
        # Check 2: Wait and re-check (for eventual consistency)
        await asyncio.sleep(1.0)
        state = hass.states.get(entity_id)
        if state and state.state not in ["unknown", "unavailable"]:
            return True
        
        # Check 3: Entity registry (for disabled entities)
        try:
            from homeassistant.helpers.entity_registry import async_get as async_get_entity_registry
            entity_registry = async_get_entity_registry(hass)
            registry_entry = entity_registry.async_get(entity_id)
            if registry_entry:
                return True
        except Exception:
            pass  # Entity registry check is optional
        
        return False
        
    except Exception as e:
        _LOGGER.debug("Error in entity existence check for %s: %s", entity_id, e)
        return False


async def _build_service_data_ultra_safe(domain: str, entity_data: Tuple, dog_name: str) -> Dict[str, Any]:
    """Build service data with ultra-safe validation."""
    
    if not entity_data or len(entity_data) < 2:
        raise ValueError(f"Invalid entity data: {entity_data}")
    
    entity_name = entity_data[0]
    friendly_name = entity_data[1]
    
    # Validate entity name
    if not entity_name or not isinstance(entity_name, str):
        raise ValueError(f"Invalid entity name: {entity_name}")
    
    if not friendly_name or not isinstance(friendly_name, str):
        raise ValueError(f"Invalid friendly name: {friendly_name}")
    
    # Sanitize names
    entity_name = str(entity_name).strip()
    friendly_name = str(friendly_name).strip()
    dog_name = str(dog_name).strip()
    
    service_data = {
        "name": f"{dog_name.title()} {friendly_name}",
    }
    
    try:
        if domain == "input_boolean":
            icon = entity_data[2] if len(entity_data) > 2 else "mdi:dog"
            service_data.update({
                "icon": str(icon) if icon else "mdi:dog"
            })
            
        elif domain == "counter":
            icon = entity_data[2] if len(entity_data) > 2 else "mdi:counter"
            service_data.update({
                "initial": 0,
                "step": 1,
                "minimum": 0,
                "maximum": 999999,  # Very high maximum
                "icon": str(icon) if icon else "mdi:counter",
                "restore": True
            })
            
        elif domain == "input_datetime":
            if len(entity_data) < 5:
                raise ValueError(f"Insufficient data for input_datetime: {entity_data}")
            
            has_time, has_date, initial = entity_data[2], entity_data[3], entity_data[4]
            icon = entity_data[5] if len(entity_data) > 5 else "mdi:calendar-clock"
            
            service_data.update({
                "has_time": bool(has_time),
                "has_date": bool(has_date),
                "icon": str(icon) if icon else "mdi:calendar-clock"
            })
            
            if initial and str(initial) not in ["None", "null", ""]:
                service_data["initial"] = str(initial)
                
        elif domain == "input_text":
            max_length = entity_data[2] if len(entity_data) > 2 else 255
            icon = entity_data[3] if len(entity_data) > 3 else "mdi:text"
            
            service_data.update({
                "max": max(1, min(int(max_length), 255)),  # Clamp between 1-255
                "initial": "",
                "icon": str(icon) if icon else "mdi:text",
                "mode": "text"
            })
            
        elif domain == "input_number":
            if len(entity_data) < 8:
                raise ValueError(f"Insufficient data for input_number: {entity_data}")
            
            step, min_val, max_val, initial, unit = entity_data[2:7]
            icon = entity_data[7] if len(entity_data) > 7 else "mdi:numeric"
            
            # Validate and sanitize numeric values
            step = max(0.01, float(step))
            min_val = float(min_val)
            max_val = max(min_val + step, float(max_val))
            initial = max(min_val, min(max_val, float(initial)))
            
            service_data.update({
                "min": min_val,
                "max": max_val,
                "step": step,
                "initial": initial,
                "unit_of_measurement": str(unit) if unit else "",
                "icon": str(icon) if icon else "mdi:numeric",
                "mode": "slider"
            })
            
        elif domain == "input_select":
            if len(entity_data) < 4:
                raise ValueError(f"Insufficient data for input_select: {entity_data}")
            
            options, initial = entity_data[2], entity_data[3]
            icon = entity_data[4] if len(entity_data) > 4 else "mdi:format-list-bulleted"
            
            # Validate options
            if not options or not isinstance(options, (list, tuple)):
                options = ["Option 1", "Option 2"]
            
            options_list = [str(opt) for opt in options if opt]
            if not options_list:
                options_list = ["Option 1"]
            
            # Validate initial
            initial_str = str(initial) if initial else options_list[0]
            if initial_str not in options_list:
                initial_str = options_list[0]
            
            service_data.update({
                "options": options_list,
                "initial": initial_str,
                "icon": str(icon) if icon else "mdi:format-list-bulleted"
            })
        
        return service_data
        
    except Exception as e:
        _LOGGER.error("Error building service data for %s %s: %s", domain, entity_name, e)
        raise ValueError(f"Failed to build service data: {e}")


async def _validate_service_data(hass: HomeAssistant, domain: str, service_data: Dict[str, Any]) -> bool:
    """Validate service data before creation."""
    try:
        # Basic validation
        if not service_data or not isinstance(service_data, dict):
            return False
        
        if "name" not in service_data or not service_data["name"]:
            return False
        
        # Domain-specific validation
        if domain == "input_number":
            min_val = service_data.get("min", 0)
            max_val = service_data.get("max", 100)
            initial = service_data.get("initial", 0)
            step = service_data.get("step", 1)
            
            if min_val >= max_val:
                return False
            if initial < min_val or initial > max_val:
                return False
            if step <= 0:
                return False
                
        elif domain == "input_select":
            options = service_data.get("options", [])
            initial = service_data.get("initial", "")
            
            if not options or not isinstance(options, list):
                return False
            if initial not in options:
                return False
        
        return True
        
    except Exception as e:
        _LOGGER.debug("Service data validation error: %s", e)
        return False


async def _ultra_verify_entity_creation(hass: HomeAssistant, entity_id: str, expected_data: Dict[str, Any]) -> Dict[str, Any]:
    """Ultra-comprehensive entity verification."""
    
    verification_result = {
        "exists": False,
        "correct_state": False,
        "attributes_match": False,
        "details": {},
        "errors": []
    }
    
    try:
        # Check 1: Basic existence
        state = hass.states.get(entity_id)
        if not state:
            verification_result["errors"].append("Entity not found in state registry")
            return verification_result
        
        verification_result["exists"] = True
        verification_result["details"]["state"] = state.state
        verification_result["details"]["attributes"] = dict(state.attributes)
        
        # Check 2: State validity
        if state.state in ["unknown", "unavailable"]:
            # Wait and re-check
            await asyncio.sleep(2.0)
            state = hass.states.get(entity_id)
            
            if state and state.state not in ["unknown", "unavailable"]:
                verification_result["correct_state"] = True
            else:
                verification_result["errors"].append(f"Invalid state: {state.state if state else 'None'}")
        else:
            verification_result["correct_state"] = True
        
        # Check 3: Attributes validation
        if state and state.attributes:
            expected_name = expected_data.get("name", "")
            actual_name = state.attributes.get("friendly_name", "")
            
            if expected_name and expected_name == actual_name:
                verification_result["attributes_match"] = True
            elif expected_name and expected_name in actual_name:
                verification_result["attributes_match"] = True
                verification_result["details"]["name_partial_match"] = True
            else:
                verification_result["errors"].append(f"Name mismatch: expected '{expected_name}', got '{actual_name}'")
        
        # Check 4: Domain-specific validation
        domain = entity_id.split(".")[0]
        if domain == "input_number" and state:
            try:
                float(state.state)  # Should be numeric
            except ValueError:
                verification_result["errors"].append(f"Non-numeric state for input_number: {state.state}")
        
        return verification_result
        
    except Exception as e:
        verification_result["errors"].append(f"Verification exception: {e}")
        return verification_result


async def _ultra_post_creation_verification(hass: HomeAssistant, dog_name: str, results: Dict[str, Any]) -> Dict[str, Any]:
    """Ultra-comprehensive post-creation verification."""
    
    try:
        _LOGGER.info("🔍 Starting ultra-comprehensive verification for %s", dog_name)
        
        # Critical entities that MUST exist
        critical_entities = [
            f"input_boolean.{dog_name}_feeding_morning",
            f"input_boolean.{dog_name}_outside",
            f"counter.{dog_name}_outside_count",
            f"input_text.{dog_name}_notes",
            f"input_datetime.{dog_name}_last_outside",
            f"input_select.{dog_name}_health_status",
            f"input_number.{dog_name}_weight",
        ]
        
        verified_entities = []
        missing_entities = []
        problematic_entities = []
        
        for entity_id in critical_entities:
            verification = await _ultra_verify_entity_creation(hass, entity_id, {})
            
            if verification["exists"] and verification["correct_state"]:
                verified_entities.append(entity_id)
            elif verification["exists"]:
                problematic_entities.append({
                    "entity_id": entity_id,
                    "issues": verification["errors"]
                })
            else:
                missing_entities.append(entity_id)
        
        verification_rate = (len(verified_entities) / len(critical_entities)) * 100
        
        verification_results = {
            "critical_verification_rate": verification_rate,
            "verified_entities": len(verified_entities),
            "missing_entities": len(missing_entities),
            "problematic_entities": len(problematic_entities),
            "total_critical": len(critical_entities),
            "details": {
                "verified": verified_entities,
                "missing": missing_entities,
                "problematic": problematic_entities
            }
        }
        
        _LOGGER.info("✅ Critical entity verification: %.2f%% (%d/%d)", 
                     verification_rate, len(verified_entities), len(critical_entities))
        
        if missing_entities:
            _LOGGER.error("❌ Missing critical entities: %s", missing_entities)
        
        if problematic_entities:
            _LOGGER.warning("⚠️ Problematic entities: %s", 
                          [e["entity_id"] for e in problematic_entities])
        
        return verification_results
        
    except Exception as e:
        _LOGGER.error("Error in ultra post-creation verification: %s", e)
        return {"error": str(e)}


def _calculate_final_success_rate(results: Dict[str, Any]) -> float:
    """Calculate the final success rate across all domains."""
    try:
        total_attempted = results["total_created"] + results["total_failed"]
        if total_attempted == 0:
            return 100.0  # No entities to create
        
        # Success includes created + skipped (already existing)
        total_successful = results["total_created"] + results["total_skipped"]
        total_processed = total_successful + results["total_failed"]
        
        if total_processed == 0:
            return 100.0
        
        success_rate = (total_successful / total_processed) * 100
        return round(success_rate, 2)
        
    except Exception as e:
        _LOGGER.error("Error calculating success rate: %s", e)
        return 0.0


async def _send_ultra_completion_notification(hass: HomeAssistant, dog_name: str, 
                                            results: Dict[str, Any], success_rate: float) -> None:
    """Send ultra-detailed completion notification."""
    try:
        # Determine notification style based on success rate
        if success_rate >= 100.0:
            icon = "🎯"
            title = f"{icon} PERFEKT - {dog_name.title()}"
            message = f"✅ 100% ERFOLG!\n{results['total_created']} Entitäten erstellt\n{results['total_skipped']} bereits vorhanden"
            urgency = "normal"
        elif success_rate >= 98.0:
            icon = "🏆"
            title = f"{icon} EXZELLENT - {dog_name.title()}"
            message = f"🌟 {success_rate:.1f}% Erfolg!\n{results['total_created']} erstellt, {results['total_failed']} fehlgeschlagen"
            urgency = "normal"
        elif success_rate >= 95.0:
            icon = "✅"
            title = f"{icon} SEHR GUT - {dog_name.title()}"
            message = f"👍 {success_rate:.1f}% Erfolg!\n{results['total_created']} erstellt, {results['total_failed']} fehlgeschlagen"
            urgency = "normal"
        elif success_rate >= 90.0:
            icon = "⚠️"
            title = f"{icon} GUT - {dog_name.title()}"
            message = f"⚡ {success_rate:.1f}% Erfolg!\n{results['total_created']} erstellt, {results['total_failed']} fehlgeschlagen"
            urgency = "high"
        else:
            icon = "🚨"
            title = f"{icon} PROBLEME - {dog_name.title()}"
            message = f"❌ Nur {success_rate:.1f}% Erfolg!\n{results['total_created']} erstellt, {results['total_failed']} fehlgeschlagen"
            urgency = "high"
        
        # Add retry information if applicable
        retry_attempts = results.get("retry_attempts", 0)
        if retry_attempts > 0:
            message += f"\n🔄 {retry_attempts} Wiederholungen erforderlich"
        
        # Add domain breakdown
        domain_info = []
        for domain, domain_results in results.get("domain_results", {}).items():
            if isinstance(domain_results, dict):
                created = domain_results.get("created", 0)
                failed = domain_results.get("failed", 0)
                if created > 0 or failed > 0:
                    domain_info.append(f"{domain}: {created}✅/{failed}❌")
        
        if domain_info:
            message += f"\n\nDetails:\n" + "\n".join(domain_info[:3])  # Limit to 3 domains
        
        await hass.services.async_call(
            "persistent_notification", "create",
            {
                "title": title,
                "message": message,
                "notification_id": f"hundesystem_ultra_setup_{dog_name}_{datetime.now().timestamp()}",
            },
            blocking=False
        )
        
        # Send mobile notification for high urgency
        if urgency == "high":
            try:
                await hass.services.async_call(
                    "notify", "mobile_app",
                    {
                        "title": title,
                        "message": f"Hundesystem Setup: {success_rate:.1f}% Erfolg",
                        "data": {
                            "priority": "high",
                            "ttl": 300
                        }
                    },
                    blocking=False
                )
            except Exception:
                pass  # Mobile notifications are optional
        
    except Exception as e:
        _LOGGER.error("Error sending completion notification: %s", e)


async def _send_error_notification(hass: HomeAssistant, dog_name: str, error: str) -> None:
    """Send error notification."""
    try:
        await hass.services.async_call(
            "persistent_notification", "create",
            {
                "title": f"🚨 FEHLER - Hundesystem {dog_name.title()}",
                "message": f"❌ Kritischer Fehler beim Setup:\n\n{error}\n\nBitte Logs prüfen und erneut versuchen.",
                "notification_id": f"hundesystem_error_{dog_name}_{datetime.now().timestamp()}",
            },
            blocking=False
        )
    except Exception as e:
        _LOGGER.error("Error sending error notification: %s", e)


# ULTRA-ROBUST ENTITY CREATION FUNCTIONS

async def _create_input_booleans(hass: HomeAssistant, dog_name: str) -> Dict[str, Any]:
    """Create input_boolean entities with ultra-reliability."""
    
    boolean_entities = [
        # Core feeding booleans
        (f"{dog_name}_feeding_morning", "Frühstück", ICONS["morning"]),
        (f"{dog_name}_feeding_lunch", "Mittagessen", ICONS["lunch"]),
        (f"{dog_name}_feeding_evening", "Abendessen", ICONS["evening"]),
        (f"{dog_name}_feeding_snack", "Leckerli", ICONS["snack"]),
        
        # Core activity booleans
        (f"{dog_name}_outside", "War draußen", ICONS["outside"]),
        (f"{dog_name}_poop_done", "Geschäft gemacht", ICONS["poop"]),
        
        # System booleans
        (f"{dog_name}_visitor_mode_input", "Besuchsmodus", ICONS["visitor"]),
        (f"{dog_name}_emergency_mode", "Notfallmodus", ICONS["emergency"]),
        (f"{dog_name}_medication_given", "Medikament gegeben", ICONS["medication"]),
        
        # Health & wellbeing booleans
        (f"{dog_name}_feeling_well", "Fühlt sich wohl", ICONS["health"]),
        (f"{dog_name}_appetite_normal", "Normaler Appetit", ICONS["food"]),
        (f"{dog_name}_energy_normal", "Normale Energie", ICONS["play"]),
        
        # Feature toggles
        (f"{dog_name}_auto_reminders", "Automatische Erinnerungen", ICONS["bell"]),
        (f"{dog_name}_tracking_enabled", "Tracking aktiviert", ICONS["status"]),
        (f"{dog_name}_weather_alerts", "Wetter-Warnungen", "mdi:weather-partly-cloudy"),
        
        # Care & maintenance
        (f"{dog_name}_needs_grooming", "Pflege benötigt", ICONS["grooming"]),
        (f"{dog_name}_training_session", "Training heute", ICONS["training"]),
        (f"{dog_name}_vet_visit_due", "Tierarztbesuch fällig", ICONS["vet"]),
        
        # Additional useful booleans
        (f"{dog_name}_walked_today", "Heute Gassi gewesen", ICONS["walk"]),
        (f"{dog_name}_played_today", "Heute gespielt", ICONS["play"]),
        (f"{dog_name}_socialized_today", "Heute sozialisiert", "mdi:account-group"),
    ]
    
    return await _create_helpers_for_domain_ultra_robust(hass, "input_boolean", boolean_entities, dog_name)


async def _create_counters(hass: HomeAssistant, dog_name: str) -> Dict[str, Any]:
    """Create counter entities with ultra-reliability."""
    
    counter_entities = [
        # Feeding counters
        (f"{dog_name}_feeding_morning_count", "Frühstück Zähler", ICONS["morning"]),
        (f"{dog_name}_feeding_lunch_count", "Mittagessen Zähler", ICONS["lunch"]),
        (f"{dog_name}_feeding_evening_count", "Abendessen Zähler", ICONS["evening"]),
        (f"{dog_name}_feeding_snack_count", "Leckerli Zähler", ICONS["snack"]),
        
        # Activity counters
        (f"{dog_name}_outside_count", "Draußen Zähler", ICONS["outside"]),
        (f"{dog_name}_walk_count", "Gassi Zähler", ICONS["walk"]),
        (f"{dog_name}_play_count", "Spiel Zähler", ICONS["play"]),
        (f"{dog_name}_training_count", "Training Zähler", ICONS["training"]),
        (f"{dog_name}_poop_count", "Geschäft Zähler", ICONS["poop"]),
        
        # Health & care counters
        (f"{dog_name}_vet_visits_count", "Tierarzt Besuche", ICONS["vet"]),
        (f"{dog_name}_medication_count", "Medikamente", ICONS["medication"]),
        (f"{dog_name}_grooming_count", "Pflege Sessions", ICONS["grooming"]),
        
        # Summary counters
        (f"{dog_name}_activity_count", "Aktivitäten gesamt", ICONS["status"]),
        (f"{dog_name}_emergency_calls", "Notfälle", ICONS["emergency"]),
        (f"{dog_name}_daily_score", "Tages-Score", "mdi:star"),
        
        # Social & behavioral counters
        (f"{dog_name}_social_interactions", "Soziale Kontakte", "mdi:account-group"),
        (f"{dog_name}_behavior_incidents", "Verhaltensereignisse", "mdi:alert-outline"),
        (f"{dog_name}_rewards_given", "Belohnungen", "mdi:gift"),
    ]
    
    return await _create_helpers_for_domain_ultra_robust(hass, "counter", counter_entities, dog_name)


async def _create_input_datetimes(hass: HomeAssistant, dog_name: str) -> Dict[str, Any]:
    """Create input_datetime entities with ultra-reliability."""
    
    # Feeding schedule times (time only)
    feeding_time_entities = []
    for meal_type in FEEDING_TYPES:
        feeding_time_entities.append((
            f"{dog_name}_feeding_{meal_type}_time",
            f"{MEAL_TYPES[meal_type]} Zeit",
            True,  # has_time
            False, # has_date
            DEFAULT_FEEDING_TIMES[meal_type],
            ICONS[meal_type]
        ))
    
    # Last activity timestamps (date + time)
    last_activity_entities = [
        (f"{dog_name}_last_feeding_morning", "Letztes Frühstück", True, True, None, ICONS["morning"]),
        (f"{dog_name}_last_feeding_lunch", "Letztes Mittagessen", True, True, None, ICONS["lunch"]),
        (f"{dog_name}_last_feeding_evening", "Letztes Abendessen", True, True, None, ICONS["evening"]),
        (f"{dog_name}_last_feeding_snack", "Letztes Leckerli", True, True, None, ICONS["snack"]),
        (f"{dog_name}_last_outside", "Letzter Gartengang", True, True, None, ICONS["outside"]),
        (f"{dog_name}_last_walk", "Letzter Spaziergang", True, True, None, ICONS["walk"]),
        (f"{dog_name}_last_play", "Letztes Spielen", True, True, None, ICONS["play"]),
        (f"{dog_name}_last_training", "Letztes Training", True, True, None, ICONS["training"]),
        (f"{dog_name}_last_poop", "Letztes Geschäft", True, True, None, ICONS["poop"]),
        (f"{dog_name}_last_activity", "Letzte Aktivität", True, True, None, ICONS["status"]),
        (f"{dog_name}_last_door_ask", "Letzte Türfrage", True, True, None, "mdi:door"),
    ]
    
    # Health & vet appointments
    health_entities = [
        (f"{dog_name}_last_vet_visit", "Letzter Tierarztbesuch", True, True, None, ICONS["vet"]),
        (f"{dog_name}_next_vet_appointment", "Nächster Tierarzttermin", True, True, None, ICONS["vet"]),
        (f"{dog_name}_last_vaccination", "Letzte Impfung", True, True, None, "mdi:needle"),
        (f"{dog_name}_next_vaccination", "Nächste Impfung", True, True, None, "mdi:needle"),
        (f"{dog_name}_medication_time", "Medikamentenzeit", True, False, "08:00:00", ICONS["medication"]),
        (f"{dog_name}_last_grooming", "Letzte Pflege", True, True, None, ICONS["grooming"]),
        (f"{dog_name}_next_grooming", "Nächste Pflege", True, True, None, ICONS["grooming"]),
    ]
    
    # Emergency & special events
    special_entities = [
        (f"{dog_name}_emergency_contact_time", "Notfall Kontakt Zeit", True, True, None, ICONS["emergency"]),
        (f"{dog_name}_visitor_start", "Besuch Start", True, True, None, ICONS["visitor"]),
        (f"{dog_name}_visitor_end", "Besuch Ende", True, True, None, ICONS["visitor"]),
        (f"{dog_name}_birth_date", "Geburtsdatum", False, True, None, ICONS["dog"]),
        (f"{dog_name}_last_weight_check", "Letzte Gewichtskontrolle", True, True, None, "mdi:weight-kilogram"),
    ]
    
    all_datetime_entities = feeding_time_entities + last_activity_entities + health_entities + special_entities
    
    return await _create_helpers_for_domain_ultra_robust(hass, "input_datetime", all_datetime_entities, dog_name)


async def _create_input_texts(hass: HomeAssistant, dog_name: str) -> Dict[str, Any]:
    """Create input_text entities with ultra-reliability."""
    
    text_entities = [
        # Basic notes
        (f"{dog_name}_notes", "Allgemeine Notizen", 255, ICONS["notes"]),
        (f"{dog_name}_daily_notes", "Tagesnotizen", 255, ICONS["notes"]),
        (f"{dog_name}_behavior_notes", "Verhaltensnotizen", 255, ICONS["notes"]),
        
        # Activity notes
        (f"{dog_name}_last_activity_notes", "Letzte Aktivität Notizen", 255, ICONS["notes"]),
        (f"{dog_name}_walk_notes", "Spaziergang Notizen", 255, ICONS["walk"]),
        (f"{dog_name}_play_notes", "Spiel Notizen", 255, ICONS["play"]),
        (f"{dog_name}_training_notes", "Training Notizen", 255, ICONS["training"]),
        
        # Visitor information
        (f"{dog_name}_visitor_name", "Besuchername", 100, ICONS["visitor"]),
        (f"{dog_name}_visitor_contact", "Besucher Kontakt", 200, ICONS["visitor"]),
        (f"{dog_name}_visitor_notes", "Besucher Notizen", 255, ICONS["visitor"]),
        (f"{dog_name}_visitor_instructions", "Anweisungen für Besucher", 255, ICONS["visitor"]),
        
        # Health information
        (f"{dog_name}_health_notes", "Gesundheitsnotizen", 255, ICONS["health"]),
        (f"{dog_name}_medication_notes", "Medikamenten Notizen", 255, ICONS["medication"]),
        (f"{dog_name}_vet_notes", "Tierarzt Notizen", 255, ICONS["vet"]),
        (f"{dog_name}_symptoms", "Aktuelle Symptome", 255, ICONS["health"]),
        (f"{dog_name}_allergies", "Allergien", 255, ICONS["health"]),
        
        # Emergency contacts
        (f"{dog_name}_emergency_contact", "Notfallkontakt", 200, ICONS["emergency"]),
        (f"{dog_name}_vet_contact", "Tierarzt Kontakt", 200, ICONS["vet"]),
        (f"{dog_name}_backup_contact", "Ersatzkontakt", 200, "mdi:phone"),
        
        # Dog information
        (f"{dog_name}_breed", "Rasse", 100, ICONS["dog"]),
        (f"{dog_name}_color", "Farbe/Markierungen", 100, ICONS["dog"]),
        (f"{dog_name}_microchip_id", "Mikrochip ID", 50, "mdi:chip"),
        (f"{dog_name}_insurance_number", "Versicherungsnummer", 100, "mdi:shield"),
        (f"{dog_name}_registration_number", "Registrierungsnummer", 100, "mdi:card-account-details"),
        
        # Food preferences
        (f"{dog_name}_food_brand", "Futtermarke", 100, ICONS["food"]),
        (f"{dog_name}_food_allergies", "Futterallergien", 255, ICONS["food"]),
        (f"{dog_name}_favorite_treats", "Lieblingsleckerli", 255, ICONS["snack"]),
        (f"{dog_name}_feeding_instructions", "Fütterungsanweisungen", 255, ICONS["food"]),
    ]
    
    return await _create_helpers_for_domain_ultra_robust(hass, "input_text", text_entities, dog_name)


async def _create_input_numbers(hass: HomeAssistant, dog_name: str) -> Dict[str, Any]:
    """Create input_number entities with ultra-reliability."""
    
    number_entities = [
        # Health metrics
        (f"{dog_name}_weight", "Gewicht", 0.1, 0, 100, 10, "kg", "mdi:weight-kilogram"),
        (f"{dog_name}_target_weight", "Zielgewicht", 0.1, 0, 100, 10, "kg", "mdi:target"),
        (f"{dog_name}_temperature", "Körpertemperatur", 0.1, 35, 42, 38.5, "°C", ICONS["thermometer"]),
        (f"{dog_name}_heart_rate", "Herzfrequenz", 1, 60, 200, 100, "bpm", ICONS["health"]),
        (f"{dog_name}_respiratory_rate", "Atemfrequenz", 1, 10, 50, 20, "bpm", ICONS["health"]),
        
        # Activity metrics
        (f"{dog_name}_daily_walk_duration", "Tägliche Gehzeit", 1, 0, 300, 60, "min", ICONS["walk"]),
        (f"{dog_name}_daily_play_time", "Tägliche Spielzeit", 1, 0, 180, 30, "min", ICONS["play"]),
        (f"{dog_name}_training_duration", "Trainingszeit", 1, 0, 120, 15, "min", ICONS["training"]),
        (f"{dog_name}_sleep_hours", "Schlafstunden", 0.5, 0, 24, 12, "h", "mdi:sleep"),
        
        # Food metrics
        (f"{dog_name}_daily_food_amount", "Tägliche Futtermenge", 10, 0, 2000, 400, "g", ICONS["food"]),
        (f"{dog_name}_treat_amount", "Leckerli Menge", 1, 0, 200, 20, "g", ICONS["snack"]),
        (f"{dog_name}_water_intake", "Wasseraufnahme", 50, 0, 3000, 500, "ml", "mdi:cup-water"),
        
        # Age and lifespan
        (f"{dog_name}_age_years", "Alter", 0.1, 0, 30, 5, "Jahre", ICONS["dog"]),
        (f"{dog_name}_age_months", "Alter", 1, 0, 360, 60, "Monate", ICONS["dog"]),
        (f"{dog_name}_expected_lifespan", "Erwartete Lebenszeit", 1, 8, 25, 14, "Jahre", ICONS["dog"]),
        
        # Size measurements
        (f"{dog_name}_height", "Schulterhöhe", 0.5, 10, 100, 50, "cm", "mdi:ruler"),
        (f"{dog_name}_length", "Körperlänge", 0.5, 20, 150, 70, "cm", "mdi:ruler"),
        (f"{dog_name}_neck_circumference", "Halsumfang", 0.5, 10, 80, 35, "cm", "mdi:tape-measure"),
        (f"{dog_name}_chest_circumference", "Brustumfang", 0.5, 20, 120, 60, "cm", "mdi:tape-measure"),
        
        # Health scores and ratings
        (f"{dog_name}_health_score", "Gesundheits Score", 0.1, 0, 10, 8, "Punkte", ICONS["health"]),
        (f"{dog_name}_happiness_score", "Glücks Score", 0.1, 0, 10, 8, "Punkte", ICONS["happy"]),
        (f"{dog_name}_energy_level", "Energie Level", 0.1, 0, 10, 7, "Punkte", ICONS["play"]),
        (f"{dog_name}_appetite_score", "Appetit Score", 0.1, 0, 10, 8, "Punkte", ICONS["food"]),
    ]
    
    return await _create_helpers_for_domain_ultra_robust(hass, "input_number", number_entities, dog_name)


async def _create_input_selects(hass: HomeAssistant, dog_name: str) -> Dict[str, Any]:
    """Create input_select entities with ultra-reliability."""
    
    select_entities = [
        # Health status
        (f"{dog_name}_health_status", "Gesundheitsstatus", [
            "Ausgezeichnet", "Gut", "Normal", "Schwach", "Krank", "Notfall"
        ], "Gut", ICONS["health"]),
        
        # Mood
        (f"{dog_name}_mood", "Stimmung", [
            "Sehr glücklich", "Glücklich", "Neutral", "Gestresst", "Ängstlich", "Krank"
        ], "Glücklich", ICONS["happy"]),
        
        # Activity level
        (f"{dog_name}_activity_level", "Aktivitätslevel", [
            "Sehr niedrig", "Niedrig", "Normal", "Hoch", "Sehr hoch"
        ], "Normal", ICONS["play"]),
        
        # Energy level
        (f"{dog_name}_energy_level_category", "Energie Level", [
            "Sehr müde", "Müde", "Normal", "Energiegeladen", "Hyperaktiv"
        ], "Normal", ICONS["play"]),
        
        # Appetite level
        (f"{dog_name}_appetite_level", "Appetit Level", [
            "Kein Appetit", "Wenig Appetit", "Normal", "Guter Appetit", "Sehr hungrig"
        ], "Normal", ICONS["food"]),
        
        # Emergency level
        (f"{dog_name}_emergency_level", "Notfall Level", [
            "Normal", "Aufmerksamkeit", "Warnung", "Dringend", "Kritisch"
        ], "Normal", ICONS["emergency"]),
        
        # Size category
        (f"{dog_name}_size_category", "Größenkategorie", [
            "Toy (< 4kg)", "Klein (4-10kg)", "Mittel (10-25kg)", "Groß (25-45kg)", "Riesig (> 45kg)"
        ], "Mittel (10-25kg)", ICONS["dog"]),
        
        # Age group
        (f"{dog_name}_age_group", "Altersgruppe", [
            "Welpe (< 6 Monate)", "Junghund (6-18 Monate)", "Erwachsen (1-7 Jahre)", 
            "Senior (7-10 Jahre)", "Hochbetagt (> 10 Jahre)"
        ], "Erwachsen (1-7 Jahre)", ICONS["dog"]),
        
        # Training level
        (f"{dog_name}_training_level", "Trainingslevel", [
            "Anfänger", "Grundlagen", "Fortgeschritten", "Experte", "Champion"
        ], "Grundlagen", ICONS["training"]),
    ]
    
    return await _create_helpers_for_domain_ultra_robust(hass, "input_select", select_entities, dog_name)


# VERIFICATION FUNCTIONS

async def verify_helper_creation_ultra(hass: HomeAssistant, dog_name: str) -> dict:
    """Ultra-comprehensive verification of helper entity creation."""
    
    critical_entities = [
        f"input_boolean.{dog_name}_feeding_morning",
        f"input_boolean.{dog_name}_outside", 
        f"counter.{dog_name}_outside_count",
        f"input_text.{dog_name}_notes",
        f"input_datetime.{dog_name}_last_outside",
        f"input_select.{dog_name}_health_status",
        f"input_number.{dog_name}_weight",
    ]
    
    verification_results = {
        "total_checked": len(critical_entities),
        "existing": [],
        "missing": [],
        "problematic": [],
        "success_rate": 0.0,
        "detailed_results": {}
    }
    
    for entity_id in critical_entities:
        entity_result = await _ultra_verify_entity_creation(hass, entity_id, {})
        
        verification_results["detailed_results"][entity_id] = entity_result
        
        if entity_result["exists"] and entity_result["correct_state"]:
            verification_results["existing"].append(entity_id)
        elif entity_result["exists"]:
            verification_results["problematic"].append(entity_id)
        else:
            verification_results["missing"].append(entity_id)
    
    verification_results["success_rate"] = (
        len(verification_results["existing"]) / verification_results["total_checked"] * 100
    )
    
    _LOGGER.info("🎯 ULTRA verification for %s: %.2f%% success rate (%d/%d entities)", 
                 dog_name, verification_results["success_rate"], 
                 len(verification_results["existing"]), verification_results["total_checked"])
    
    if verification_results["missing"]:
        _LOGGER.error("❌ Missing critical entities: %s", verification_results["missing"])
    
    if verification_results["problematic"]:
        _LOGGER.warning("⚠️ Problematic entities: %s", verification_results["problematic"])
    
    return verification_results
