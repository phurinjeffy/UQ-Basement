
import { useState } from "react";
import AddCourses from "../components/AddCourses";

function Home() {
  const [showAddCourses, setShowAddCourses] = useState(false);

  return (
    <div className="flex justify-center items-center py-16">
      <div className="hero bg-base-200 rounded-xl shadow-xl p-8 max-w-3xl w-full mx-auto">
        {!showAddCourses ? (
          <div className="flex flex-col lg:flex-row gap-8 items-center justify-between">
            <div className="flex-1 text-center lg:text-left">
              <h1 className="text-5xl font-bold">Welcome to UQ basement</h1>
              <p className="py-6">
                Provident cupiditate voluptatem et in. Quaerat fugiat ut assumenda excepturi exercitationem
                quasi. In deleniti eaque aut repudiandae et a id nisi.
              </p>
            </div>
            <div className="flex-1 flex justify-center">
              <div className="card bg-base-100 w-full max-w-sm shrink-0 shadow-2xl">
                <div className="card-body">
                  <fieldset className="fieldset">
                    <label className="label">UQ Student ID</label>
                    <input type="email" className="input" placeholder="s4123456" />
                    <label className="label">Password</label>
                    <input type="password" className="input" placeholder="Password" />
                    <div><a className="link link-hover">Forgot password?</a></div>
                    <button className="btn btn-neutral mt-4" onClick={() => setShowAddCourses(true)}>Continue</button>
                  </fieldset>
                </div>
              </div>
            </div>
          </div>
        ) : (
          <AddCourses />
        )}
      </div>
    </div>
  );
}

export default Home;
