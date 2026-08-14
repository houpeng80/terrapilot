from backend.leader_agent.leader_agent import LeaderAgent

def main():
    print(f"--- Terraform pilot Agent open ---")
    config = {"configurable": {"thread_id": "default_thread_id2", "user_id": "user_test_2"}}

    agent = LeaderAgent(config)

    agent.invoke()

    print(f"--- Terraform pilot Agent close ---")

if __name__ == "__main__":
    main()