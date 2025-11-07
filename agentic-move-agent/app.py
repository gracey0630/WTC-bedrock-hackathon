import streamlit as st
import json
from PIL import Image, ImageDraw, ImageFont
import io
from datetime import datetime
from agents.inventory_agent import InventoryAgent
from orchestrator_agent import OrchestratorAgent

# Color palette for segmentation
COLORS = [
    "#FF6B6B", "#4ECDC4", "#45B7D1", "#FFA07A", 
    "#98D8C8", "#F7DC6F", "#BB8FCE", "#85C1E2",
    "#F8B739", "#52B788", "#E76F51", "#2A9D8F"
]

def generate_color_for_item(index):
    """Assign consistent color to each item"""
    return COLORS[index % len(COLORS)]

def draw_segmented_image(image, items):
    img = image.convert('RGBA')
    overlay = Image.new('RGBA', img.size, (255,255,255,0))
    draw = ImageDraw.Draw(overlay)
    
    try:
        font = ImageFont.truetype("arial.ttf", 20)
    except:
        font = ImageFont.load_default()
    
    for idx, item in enumerate(items):
        color = generate_color_for_item(idx)
        bbox = item.get('bbox')
        if not bbox or len(bbox) != 4:
            continue
        
        x1, y1, x2, y2 = bbox  # assuming absolute pixels
        rgb = tuple(int(color[i:i+2],16) for i in (1,3,5))
        
        draw.rectangle([x1, y1, x2, y2], fill=(*rgb,60), outline=color, width=4)
        
        # Draw label
        label = f"{idx+1}. {item['name']}"
        bbox_text = draw.textbbox((x1, y1-30), label, font=font)
        padding = 8
        draw.rectangle([bbox_text[0]-padding, bbox_text[1]-padding, 
                        bbox_text[2]+padding, bbox_text[3]+padding],
                       fill=color)
        draw.text((x1, y1-30), label, fill="white", font=font)
    
    return Image.alpha_composite(img, overlay).convert('RGB')


def main():
    st.set_page_config(page_title="Moving Assistant", page_icon="🚚", layout="wide")
    
    # Header
    st.title("AI Moving Assistant with Bedrock")
    st.markdown("### Upload → AI Analysis → Color-Coded Segmentation → Inventory Management")
    
    # Initialize session state
    if 'session_id' not in st.session_state:
        st.session_state.session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    if 'inventory_agent' not in st.session_state:
        st.session_state.inventory_agent = InventoryAgent(st.session_state.session_id)
    if 'inventory' not in st.session_state:
        st.session_state.inventory = []
    if 'segmented_images' not in st.session_state:
        st.session_state.segmented_images = []
    if 'original_images' not in st.session_state:
        st.session_state.original_images = []
    
    # Initialize user inputs
    if 'from_location' not in st.session_state:
        st.session_state.from_location = ""
    if 'to_location' not in st.session_state:
        st.session_state.to_location = ""
    if 'budget' not in st.session_state:
        st.session_state.budget = 3000
    
    # Initialize orchestrator results
    if 'orchestrator_summary' not in st.session_state:
        st.session_state.orchestrator_summary = None
    if 'plan_generated' not in st.session_state:
        st.session_state.plan_generated = False
    
    # Sidebar
    with st.sidebar:
        st.header("📋 Session Info")
        st.code(st.session_state.session_id)

        st.title("Moving Assistant")

        # Use session state for inputs so they persist
        from_location = st.text_input(
            "Moving from", 
            value=st.session_state.from_location,
            key="from_input",
            placeholder="e.g., 971 Columbus Ave, NYC"
        )
        to_location = st.text_input(
            "Moving to", 
            value=st.session_state.to_location,
            key="to_input",
            placeholder="e.g., Brooklyn, NY"
        )
        budget = st.number_input(
            "Budget ($)", 
            min_value=100, 
            value=st.session_state.budget, 
            step=100,
            key="budget_input"
        )

        # Save to session state
        st.session_state.from_location = from_location
        st.session_state.to_location = to_location
        st.session_state.budget = budget

        st.divider()

        # Generate Moving Plan button with ALL fixes
        if st.button("🚀 Generate Moving Plan", type="primary", use_container_width=True):
            # Validation: Check if photos were analyzed
            if not st.session_state.get('inventory') or len(st.session_state.inventory) == 0:
                st.error("⚠️ Please upload and analyze photos first!")
                st.info("👉 Go to 'Step 1: Upload' tab and click 'Analyze All Photos'")
            elif not from_location or not to_location:
                st.error("⚠️ Please fill in both 'From' and 'To' locations")
            else:
                with st.spinner("🤖 Generating comprehensive moving plan..."):
                    # ✅ FIX 1: Define user_request BEFORE using it
                    user_request = {
                        "from": from_location,
                        "to": to_location,
                        "budget": budget,
                        "priority": "minimize cost"
                    }
                    
                    # ✅ FIX 2: Add try block
                    try:
                        # ✅ FIX 3: Pass inventory as parameter to orchestrator
                        orchestrator = OrchestratorAgent(
                            user_request=user_request,
                            session_id=st.session_state.session_id,
                            inventory=st.session_state.inventory  # ← KEY FIX!
                        )
                        
                        # Execute the plan
                        summary = orchestrator.execute_move()
                        
                        # Check if successful
                        if summary.get('status') == 'failed':
                            st.error(f"❌ {summary.get('error')}")
                            st.info(summary.get('message', ''))
                        else:
                            # Save summary to session state
                            st.session_state.orchestrator_summary = summary
                            st.session_state.plan_generated = True
                            
                            # Update inventory with decisions from orchestrator
                            if 'current_state' in summary and 'inventory' in summary['current_state']:
                                st.session_state.inventory = summary['current_state']['inventory']
                            
                            st.success("✅ Moving plan generated successfully!")
                            st.balloons()
                            
                            # Show summary
                            with st.expander("📊 View Complete Summary", expanded=True):
                                st.json(summary)
                    
                    except Exception as e:
                        st.error(f"❌ Plan generation failed: {str(e)}")
                        import traceback
                        st.code(traceback.format_exc())
        
        # Display plan status
        if st.session_state.plan_generated:
            st.success("✅ Moving plan generated!")
            if st.session_state.orchestrator_summary:
                summary = st.session_state.orchestrator_summary
                # ✅ FIX 4: Use correct nested structure
                item_summary = summary.get('item_summary', {})
                cost_analysis = summary.get('cost_analysis', {})
                
                st.info(f"""
                **Plan Summary:**
                - Total Items: {item_summary.get('total_items', 0)}
                - Items to Move: {item_summary.get('items_to_move', 0)}
                - Items to Replace: {item_summary.get('items_to_replace', 0)}
                - Net Cost: ${cost_analysis.get('net_cost', 0):.2f}
                """)
        
        st.divider()
        
        st.header("Workflow Steps")
        st.markdown("""
        1. ✅ **Upload Photos**
        2. 🔍 **AI Analysis** (Bedrock Vision)
        3. 🎨 **Segmentation** (Bounding Boxes)
        4. 🎯 **Generate Plan** (Decision AI)
        5. 📊 **Review Results**
        """)
        
        st.divider()
        
        if st.session_state.inventory:
            st.success(f"✅ {len(st.session_state.inventory)} items detected")
        
        if st.button("🔄 Reset Session", type="secondary"):
            st.session_state.clear()
            st.rerun()
    
    # Main workflow tabs
    tabs = st.tabs([
        "Step 1: Upload", 
        "Step 2: Segmentation" , 
        "Step 3: Total Inventory", 
        "Step 4: Planning"
    ])
    
    # ========== TAB 1: Upload & Analyze ==========
    with tabs[0]:
        st.header("Upload Room Photos")
        
        uploaded_files = st.file_uploader(
            "Upload clear photos of your rooms (PNG, JPG, JPEG)",
            type=["png", "jpg", "jpeg"],
            accept_multiple_files=True,
            help="Take photos showing furniture clearly from different angles"
        )
        
        if uploaded_files:
            st.success(f"✅ {len(uploaded_files)} photo(s) uploaded")
            
            # Preview thumbnails
            cols = st.columns(min(len(uploaded_files), 4))
            for idx, file in enumerate(uploaded_files[:4]):
                with cols[idx]:
                    image = Image.open(file)
                    st.image(image, caption=f"Photo {idx+1}", use_container_width=True)
            
            if len(uploaded_files) > 4:
                st.info(f"+ {len(uploaded_files) - 4} more photos")
            
            st.divider()
            
            # Analyze button
            if st.button("🔍 Analyze All Photos with Bedrock AI", type="primary", use_container_width=True):
                with st.spinner("🤖 Running AI analysis..."):
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    # Reset state
                    st.session_state.inventory = []
                    st.session_state.segmented_images = []
                    st.session_state.original_images = []
                    
                    # Prepare photos for analysis
                    photo_objects = []
                    for idx, file in enumerate(uploaded_files):
                        status_text.text(f"📤 Loading photo {idx+1}/{len(uploaded_files)}...")
                        
                        # Reset file pointer
                        file.seek(0)
                        
                        # Open image with PIL
                        image = Image.open(file)
                        st.session_state.original_images.append(image.copy())
                        
                        # Convert PIL Image to BytesIO for Bedrock
                        img_byte_arr = io.BytesIO()
                        image.save(img_byte_arr, format='PNG')
                        img_byte_arr.seek(0)  # Reset pointer to beginning
                        
                        # Append the BytesIO object
                        photo_objects.append(img_byte_arr)
                        
                        progress_bar.progress((idx + 1) / (len(uploaded_files) * 2))
                    
                    # Call InventoryAgent
                    status_text.text("🔍 Running Bedrock Vision analysis...")
                    
                    try:
                        result = st.session_state.inventory_agent.analyze_photos(photo_objects)
                        
                        if result['status'] == 'success':
                            st.session_state.inventory = result['state_update']['inventory']

                            # Generate segmented images
                            status_text.text("🎨 Generating segmentation...")
                            
                            # Group items by photo (simplified - assign evenly)
                            if len(st.session_state.inventory) > 0:
                                items_per_photo = max(1, len(st.session_state.inventory) // len(uploaded_files))
                                
                                for idx, image in enumerate(st.session_state.original_images):
                                    start_idx = idx * items_per_photo
                                    end_idx = start_idx + items_per_photo if idx < len(uploaded_files) - 1 else len(st.session_state.inventory)
                                    items_for_this_photo = st.session_state.inventory[start_idx:end_idx]
                                    
                                    segmented = draw_segmented_image(image, items_for_this_photo)
                                    st.session_state.segmented_images.append(segmented)
                                    
                                    progress_bar.progress((len(uploaded_files) + idx + 1) / (len(uploaded_files) * 2))
                            
                            status_text.empty()
                            progress_bar.empty()
                            
                            st.success(f"🎉 Analysis complete! Detected {len(st.session_state.inventory)} items")
                            st.info("👉 Now go to sidebar and click '🚀 Generate Moving Plan'")
                            st.balloons()
                        else:
                            st.error(f"❌ Analysis failed: {result.get('error')}")
                    
                    except Exception as e:
                        st.error(f"❌ Analysis failed: {str(e)}")
                        import traceback
                        st.code(traceback.format_exc())
        else:
            st.info("👆 Upload photos to begin analysis")
            st.markdown("""
            **Tips for best results:**
            - Take photos in good lighting
            - Show furniture clearly from different angles
            - Include multiple rooms if needed
            - Avoid blurry or dark photos
            """)
    
    #========== TAB 2: Segmented View ==========
    with tabs[1]:
        st.header("Inventory")
        
        if st.session_state.segmented_images and st.session_state.inventory:
            for img_idx, seg_img in enumerate(st.session_state.segmented_images):
                st.subheader(f"📷 Photo {img_idx + 1}")
                
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.image(seg_img, use_container_width=True)
                
                with col2:
                    st.markdown("**Detected Items:**")
                    
                    # Show items for this photo
                    items_per_photo = max(1, len(st.session_state.inventory) // len(st.session_state.segmented_images))
                    start = img_idx * items_per_photo
                    end = start + items_per_photo if img_idx < len(st.session_state.segmented_images) - 1 else len(st.session_state.inventory)
                    
                    for i in range(start, end):
                        if i < len(st.session_state.inventory):
                            item = st.session_state.inventory[i]
                            color = generate_color_for_item(i)
                            
                            st.markdown(f"""
                            <div style="border-left: 5px solid {color}; padding-left: 12px; margin: 8px 0; background: rgba(0,0,0,0.05); padding: 8px; border-radius: 4px;">
                                <strong style="font-size: 16px;">{i+1}. {item['name']}</strong><br/>
                                 {item.get('description', 'N/A')}<br/>
                                
                            </div>
                            """, unsafe_allow_html=True)
                
                st.divider()
            
            # Download segmented images
            # if st.button(" Download All Segmented Images"):
            #     st.info("Images displayed above - right-click to save")
        # else:
        #     st.info("👆 Analyze photos first to see segmentation!")
    
    # ========== TAB 3: Inventory List ==========
    with tabs[2]:
        st.header("Complete Inventory with AI Decisions")
        
        if st.session_state.inventory:
            # Summary metrics
            col1, col2, col3, col4 = st.columns(4)
            total_volume = sum(item.get('volume', 0) for item in st.session_state.inventory)
            
            col1.metric("📦 Total Items", len(st.session_state.inventory))
            # col2.metric("📊 Total Volume", f"{total_volume:.1f} cu ft")
            col3.metric("🚚 Est. Moving Cost", f"${total_volume * 1.5:.0f}")
            
            if total_volume > 0:
                col4.metric("💰 Avg per Item", f"${(total_volume * 1.5) / len(st.session_state.inventory):.0f}")
            
            st.divider()
            
            # Search and filter
            search = st.text_input("🔍 Search items", placeholder="e.g., Sofa, Table...")
            
            # Detailed inventory
            st.subheader("Item Details")
            
            for idx, item in enumerate(st.session_state.inventory):
                # Filter by search
                if search and search.lower() not in item.get('name', '').lower():
                    continue
                
                color = generate_color_for_item(idx)
                
                # Show AI decision if available
                disposition = item.get('disposition', 'Not decided')
                disposition_icon = {"MOVE": "🚚", "SELL_AND_REPLACE": "💰", "DONATE": "❤️"}.get(disposition, "❓")
                
                with st.expander(
                    f"**{idx+1}. {item.get('name', 'Unknown')}** {disposition_icon} {disposition}", 
                    expanded=False
                ):
                    col1, col2 = st.columns([1, 3])
                    
                    with col1:
                        st.markdown(f"""
                        **Color:**  
                        <div style="width:80px; height:80px; background-color:{color}; 
                        border:3px solid #333; border-radius:8px; margin: 10px 0;"></div>
                        """, unsafe_allow_html=True)
                    
                    with col2:
                        st.write(f"**Description:** {item.get('description', 'N/A')}")
                        st.write(f"**Notes:** {item.get('notes', 'No notes')}")
                        
                        # Show AI decision details if available
                        if 'reasoning' in item:
                            st.info(f"**AI Reasoning:** {item['reasoning']}")
                        
                        if 'moving_cost' in item:
                            st.write(f"**Moving Cost:** ${item['moving_cost']:.2f}")
                        if 'amazon_price' in item:
                            st.write(f"**Amazon Price (new):** ${item['amazon_price']:.2f}")
                        if 'selling_price' in item:
                            st.write(f"**Est. Selling Price:** ${item['selling_price']:.2f}")
                        if 'savings' in item and item['savings'] > 0:
                            st.success(f"**Savings:** ${item['savings']:.2f}")
            
            st.divider()
            
            # Download JSON
            col1, col2 = st.columns(2)
            with col1:
                json_str = json.dumps(st.session_state.inventory, indent=2)
                st.download_button(
                    label="📥 Download Inventory JSON",
                    data=json_str,
                    file_name=f"inventory_{st.session_state.session_id}.json",
                    mime="application/json",
                    use_container_width=True
                )
            
            # with col2:
            #     if st.button("📊 Generate Report", use_container_width=True):
            #         st.info("Report generation coming soon!")
        else:
            st.info("👆 Analyze photos to generate inventory!")
    
    # ========== TAB 4: Move Planning ==========
    with tabs[3]:
        st.header("Moving Plan & Cost Analysis")
        
        # Show saved moving details
        if st.session_state.from_location and st.session_state.to_location:
            st.info(f"""
            **Move Details:**
            - From: {st.session_state.from_location}
            - To: {st.session_state.to_location}
            - Budget: ${st.session_state.budget:,}
            """)
        
        if st.session_state.inventory:
            # Categorize items based on AI decisions
            items_to_move = [i for i in st.session_state.inventory if i.get('disposition') == 'MOVE']
            items_to_replace = [i for i in st.session_state.inventory if i.get('disposition') == 'SELL_AND_REPLACE']
            items_to_donate = [i for i in st.session_state.inventory if i.get('disposition') == 'DONATE']
            
            # Summary metrics
            if len(items_to_move) + len(items_to_replace) + len(items_to_donate) > 0:
                col1, col2, col3 = st.columns(3)
                total_decided = len(items_to_move) + len(items_to_replace) + len(items_to_donate)
                col1.metric("🚚 Items to Move", len(items_to_move), 
                           delta=f"{len(items_to_move)/max(1,total_decided)*100:.0f}%")
                col2.metric("💰 Items to Replace", len(items_to_replace), 
                           delta=f"{len(items_to_replace)/max(1,total_decided)*100:.0f}%")
                col3.metric("❤️ Items to Donate", len(items_to_donate), 
                           delta=f"{len(items_to_donate)/max(1,total_decided)*100:.0f}%")
                
                st.divider()
            
            # Financial breakdown
            if st.session_state.orchestrator_summary:
                st.subheader("💵 Cost Analysis")
                
                cost_analysis = st.session_state.orchestrator_summary.get('cost_analysis', {})
                
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Moving Cost", f"${cost_analysis.get('total_moving_cost', 0):.2f}")
                col2.metric("Replacement Cost", f"${cost_analysis.get('total_replacement_cost', 0):.2f}")
                col3.metric("Selling Revenue", f"${cost_analysis.get('total_selling_revenue', 0):.2f}", 
                           delta=f"+${cost_analysis.get('total_selling_revenue', 0):.2f}")
                col4.metric("Net Cost", f"${cost_analysis.get('net_cost', 0):.2f}")
                
                # Budget comparison
                budget_remaining = cost_analysis.get('budget_remaining', 0)
                if budget_remaining >= 0:
                    st.success(f"✅ ${budget_remaining:.2f} under budget")
                else:
                    st.error(f"⚠️ ${abs(budget_remaining):.2f} over budget")
                
                # Savings
                total_savings = cost_analysis.get('total_savings', 0)
                if total_savings > 0:
                    st.info(f"💰 Total savings from AI optimization: ${total_savings:.2f}")
            
            # Timeline
            st.divider()
            st.subheader("📅 Suggested Timeline")
            
            if st.session_state.orchestrator_summary and 'timeline' in st.session_state.orchestrator_summary:
                timeline = st.session_state.orchestrator_summary['timeline']
                for idx, task in enumerate(timeline, 1):
                    st.markdown(f"**{idx}.** {task}")
            else:
                # Default timeline
                timeline = [
                    ("🗓️ Week 1", "List items for sale, get moving quotes"),
                    ("🗓️ Week 2", "Follow up on sales, book moving company"),
                    ("🗓️ Week 3", "Donate unsold items, pack belongings"),
                    ("🗓️ Week 4", "Moving day! Coordinate movers")
                ]
                for week, task in timeline:
                    st.markdown(f"**{week}:** {task}")
            
            # Checklist
            if st.session_state.orchestrator_summary and 'checklist' in st.session_state.orchestrator_summary:
                st.divider()
                st.subheader("✅ Moving Checklist")
                checklist = st.session_state.orchestrator_summary['checklist']
                for item in checklist:
                    st.markdown(item)
            
            # Action button
            st.divider()
            if st.button("📥 Download Complete Plan", type="primary", use_container_width=True):
                if st.session_state.orchestrator_summary:
                    plan_json = json.dumps(st.session_state.orchestrator_summary, indent=2)
                    st.download_button(
                        label="Download Plan as JSON",
                        data=plan_json,
                        file_name=f"moving_plan_{st.session_state.session_id}.json",
                        mime="application/json"
                    )
                else:
                    st.warning("Generate a moving plan first!")
        else:
            st.info("👆 Complete inventory analysis first!")

if __name__ == "__main__":
    main()