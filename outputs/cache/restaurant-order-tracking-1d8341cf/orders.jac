"""Single Order Tracking for a Restaurant."""

import from byllm.llm {Model}


glob llm = Model(model_name="gemini/gemini-2.0-flash", verbose=False);


def generate_order_status(item_name: str, stage_name: str) -> str by llm();


walker OrderAgent {
    has item_name: str;
    has order_id: int;

    can start with `root entry;
    can process_stage with order_stage entry;
}

node order_stage {
    has stage_name: str;
}


with entry {

    start = order_stage(stage_name="PLACED");
    prep = order_stage(stage_name="PREPARING");
    ready = order_stage(stage_name="READY");
    deliver = order_stage(stage_name="DELIVERED"); 

    root ++> start ++> prep ++> ready ++> deliver;

    root spawn OrderAgent(item_name="French Fries", order_id=201);
    root spawn OrderAgent(item_name="Chapati & Beef", order_id=202);
    
}


impl OrderAgent.start {
    visit [root --> (`?order_stage)];
}

impl OrderAgent.process_stage {
    current_stage = here.stage_name;
    status_message = generate_order_status(self.item_name, current_stage);
    print(f"ORDER {self.order_id}: {status_message}");

    
    if current_stage != "DELIVERED" {
        input(f"--- Press ENTER to move {self.item_name} to the next stage... ---");
        visit [-->];
    } else {
        print(f"ORDER {self.order_id} : {self.item_name} workflow is complete.");
        disengage; 
    }
}